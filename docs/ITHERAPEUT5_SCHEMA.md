# iTherapeut 5.0 — Schema & Billing Mechanisms Extraction

> **Source**: 5 FileMaker .fmp12 files in `itherapeut5/`
> **Extracted by**: Binary string analysis + Quick Start Guide V5.5 (PDF)
> **Purpose**: Reproduce billing mechanisms in iTherapeut 6.0 (SVLBH Demandes)

---

## 1. File Structure

| File | Size | Role |
|------|------|------|
| `iTherapeut.fmp12` | 30 MB | Main structure: scripts, layouts, relationships, DayBack calendar |
| `iTherapeut_Data.fmp12` | 87 MB | Data separation: patient/session/invoice data + XSLT templates for XML export |
| `iTherapeut_Print.fmp12` | 5 MB | Print layouts: Rechnung, Rückforderungsbeleg, QR-Rechnung, Mahnungen |
| `iTherapeut_Statistik.fmp12` | 1.4 MB | Statistics/reports |
| `Fibu.fmp12` | 2.4 MB | Simple accounting (Finanzbuchhaltung) |

FileMaker data separation model: structure in iTherapeut.fmp12, data in iTherapeut_Data.fmp12.

---

## 2. Core Entities (Tables)

### 2.1 Adressen (Addresses / Contacts / Patients)

Fields extracted from XML templates:

```
patient_person_givenname       → first_name
patient_person_familyname      → last_name
patient_person_salutation      → salutation (Herr/Frau)
patient_person_title           → title (Dr., etc.)
patient_person_street          → street
patient_person_pobox           → po_box
patient_person_zip             → postal_code
patient_person_zip_countrycode → country
patient_person_zip_statecode   → canton
patient_person_city            → city
patient_person_subadressing    → c/o or additional address
patient_person_phone           → phone
patient_person_fax             → fax
patient_person_email           → email
patient_person_url             → website
patient_birthdate              → date_of_birth
patient_gender                 → gender (1=male, 2=female)
patient_ssn                    → AVS/AHV number (756.xxxx.xxxx.xx)
patient_card_cardId            → insurance card number
patient_card_expiryDate        → card expiry
patient_card_validationDate    → card validation date
patient_card_validationId      → card validation ID
patient_card_validationServer  → card validation server
```

**Required for barcode/QR**: PLZ + Geburtsdatum

### 2.2 Therapeuten (Practitioners)

```
biller_person_givenname        → first_name
biller_person_familyname       → last_name
biller_person_salutation       → salutation
biller_person_title            → title
biller_person_street           → street
biller_person_pobox            → po_box
biller_person_zip              → postal_code
biller_person_city             → city
biller_person_phone            → phone
biller_person_email            → email
biller_company_companyname     → practice_name
biller_company_department      → department
biller_company_street          → practice_street
biller_company_zip             → practice_postal_code
biller_company_city            → practice_city
biller_zsr                     → ZSR/RCC number (CRITICAL)
biller_eanParty                → EAN/GLN number
biller_uidNumber               → UID number (CHE-xxx.xxx.xxx)
biller_speciality              → therapy method code
```

**Multi-practitioner**: Each practitioner has own ZSR number. Multiple practitioners per license require separate user licenses. "Sync" flag per therapist for digital invoicing.

### 2.3 Provider (Service Provider — may differ from Biller)

```
provider_person_givenname      → first_name (treating therapist)
provider_person_familyname     → last_name
provider_zsr                   → ZSR number of actual provider
provider_eanParty              → GLN
provider_speciality            → therapy method
provider_company_*             → practice details (if different from biller)
```

**Key distinction**: `biller` = who bills (practice/cabinet), `provider` = who treated (therapist). Important for multi-practitioner cabinets.

### 2.4 Sitzungen (Sessions / Treatments)

From service records:

```
record_recordId               → unique line item ID
record_tariffType             → "590" (Tarif 590 complementary therapy)
record_code                   → tarif code (method code)
record_refcode                → reference code
record_name                   → service description
record_dateBegin              → session start date
record_dateEnd                → session end date
record_session                → session number within series
record_quantity               → quantity (5-min units)
record_amount                 → line amount (CHF)
record_unit                   → unit of measure
record_unitFactor             → unit price factor
record_externalFactor         → external factor (Taxpunktwert)
record_obligation             → mandatory (KVG) vs voluntary (VVG)
record_vatRate                → VAT rate (0 = exempt for therapy)
record_sectionCode            → section code
record_providerId             → ZSR of treating therapist
record_responsibleId          → ZSR of responsible therapist
record_serviceAttributes      → additional attributes
record_validate               → validation flag
record_remark                 → remarks/notes
```

**Serien (Series)**: Groups of sessions for same patient, same insurance type. Can be open (ongoing) or closed. Required when:
- Multiple therapists treat same patient
- Patient has both KVG and VVG coverage

**Tarif 590 pricing**: Quantity × 5-minute units. Standard method from tarif590.ch catalog.

### 2.5 Rechnungen (Invoices)

From XML and guide:

```
invoice_requestId             → invoice number (sequential)
invoice_requestDate           → invoice date
invoice_requestTimestamp      → creation timestamp
invoicingType                 → tiers_garant | tiers_payant
document_number               → document sequential number
document_title                → document title
document_filename             → generated filename
document_mimeType             → application/pdf or application/xml
document_base64               → base64-encoded document content
```

**Payload control**:
```
payload_type                  → invoice type
payload_copy                  → copy flag (original/copy)
payload_storno                → cancellation/storno flag
```

---

## 3. Invoice Types (Rechnungstypen)

### 3.1 Tiers Garant (Rückforderungsbeleg — Patient pays)

`<invoice:tiers_garant>`

**Flow**: Therapist → Patient → Patient submits to insurance for reimbursement.

This is the standard for complementary therapy (Tarif 590). The patient receives:
1. **Rechnung** (invoice) from therapist — patient pays this
2. **Rückforderungsbeleg** (reimbursement claim) — patient sends to insurance

Key fields:
```
tiersGarant_paymentPeriod     → payment deadline (days)
```

### 3.2 Tiers Payant (Insurance pays directly)

`<invoice:tiers_payant>`

**Flow**: Therapist → Insurance pays directly (rare for complementary therapy).

Used mainly by physiotherapists/ergotherapists with Tarif TPW.

---

## 4. Print Formats (Druckformulare)

| Format | Description |
|--------|-------------|
| **QR 1** | Invoice with total amount + QR code only (no line items) |
| **QR 2** | Invoice with max 10 positions + QR code |
| **Rechnung** | Invoice without QR (plain) |
| **Tarifrechnung** | Rückforderungsbeleg for insurance (official Tarif 590 format) |
| **Original** | Original invoice for patient |
| **Kopie** | Copy for therapist records |
| **Rückforderungsbeleg** | Insurance reimbursement form |

Each format has separate printer/paper tray settings.

---

## 5. Payment Methods (Zahlungsarten)

### 5.1 QR-Rechnung (QR-facture SIX v2.4)

`<invoice:esrQR>`

```
esrQR_type                    → QR type
esrQR_iban                    → IBAN for QR payment
esrQR_referenceNumber         → 27-digit QR reference number
esrQR_paymentReason           → payment reason text
esrQR_customerNote            → customer note
```

**Requirements for QR generation**:
- Patient PLZ + Geburtsdatum filled
- Therapist ZSR number configured
- IBAN configured

**QR-Modul**: Generates reference number + QR code. Supports camt.054 bank file import for automated payment matching.

### 5.2 ESR Red (Legacy Orange BVR)

`<invoice:esrRed>`

```
esrRed_codingLine             → ESR coding line (bottom of slip)
esrRed_esrAttributes          → ESR attributes
esrRed_iban                   → IBAN
esrRed_paymentReason          → payment reason
esrRed_paymentTo              → payment recipient
esrRed_postAccount            → PostFinance account
esrRed_referenceNumber        → ESR reference number
```

### 5.3 ESR9 (Bank-based)

`<invoice:esr9>`

```
esr9_type                     → ESR9 type code
esr_type                      → global ESR type selector
```

### 5.4 Barzahlung (Cash Payment)

From Quick Start Guide (p.13, p.16):

**Flow**:
1. Open session → click "Sitzung Abrechnen" (bill session)
2. Select payment type = "Barzahlung" (cash)
3. iTherapeut creates invoice with **today's date as payment date**
4. Prints **Zahlungsbeleg** (payment receipt) + **Rückforderungsbeleg** (reimbursement claim)

**Rule**: Barzahlung = 1 invoice + 1 Rückforderungsbeleg for all sessions/services.

---

## 6. Mahnungen (Payment Reminders)

### 6.1 Reminder Workflow

From Quick Start Guide (p.17-18):

1. Navigate to "Rechnungen suchen, mahnen, drucken"
2. Click "zeige anzumahnende Rechnungen" → shows overdue invoices
3. Select with "markieren"
4. Click "Markierte Mahnen" → marks as reminder + prints

### 6.2 Reminder Fields

```
balance_amountReminder        → reminder surcharge amount (CHF)
```

XML attributes:
```
reminder_level                → escalation level (1st, 2nd, 3rd reminder)
reminder_text                 → reminder text body
```

### 6.3 Reminder Texts

Configured in Settings → Rechnungen → allgemeine Einstellungen:
- Template texts for Rechnung, Mahnung 1, Mahnung 2, Mahnung 3
- Conditions (Konditionen) text
- Signature/closing text

---

## 7. Sequential Numbering (Rechnungsnummern)

From Quick Start Guide (p.6):

- **Start value** configured in Settings → Rechnungen → allgemeine Einstellungen
- **Rechnungslauf-Nr.** (invoice run number) — batch number for grouped invoice printing
- **Rechnungsnummer** — sequential invoice number
- Numbers are **never reused** (even if invoice is cancelled/storno)

### 7.1 Numbering in iTherapeut 6.0 Mapping

| iTherapeut 5 | iTherapeut 6.0 |
|-------------|----------------|
| Rechnungsnummer | `ITH-YYYY-NNNN` (invoices table) |
| Tarif 590 Nr. | `T590-YYYY-NNNN` (tarif590_invoices table) |
| Re-Lauf-Nr. | Not yet implemented (batch run number) |

---

## 8. Balance & Payment Tracking

```
balance_amount                → total invoice amount
balance_amountDue             → amount still due (outstanding)
balance_amountObligations     → mandatory (KVG) portion
balance_amountPrepaid         → prepaid amount (Vorauszahlung/Barzahlung)
balance_amountReminder        → reminder surcharge
balance_currency              → currency (always CHF)
```

**Payment matching**: 
- Manual: Enter payment date in "zeige offene Debitoren" view
- Automated: Import camt.054 bank file (ISO 20022) to match QR reference numbers

---

## 9. Insurance Law Types (Versicherungsgesetze)

Swiss healthcare has multiple insurance frameworks. Each has separate billing rules:

| Code | Law | German | Description | Fields |
|------|-----|--------|-------------|--------|
| **KVG** | LAMal | Obligatorische Krankenversicherung | Mandatory health insurance | kvg_caseDate, kvg_caseId, kvg_contractNumber, kvg_insuredId |
| **VVG** | LCA | Zusatzversicherung | Supplementary insurance | vvg_caseDate, vvg_caseId, vvg_contractNumber, vvg_insuredId |
| **UVG** | LAA | Unfallversicherung | Accident insurance | uvg_caseDate, uvg_caseId, uvg_contractNumber, uvg_insuredId, uvg_ssn |
| **IVG** | LAI | Invalidenversicherung | Disability insurance | ivg_caseDate, ivg_caseId, ivg_contractNumber, ivg_nif, ivg_ssn |
| **MVG** | LAM | Militärversicherung | Military insurance | mvg_caseDate, mvg_caseId, mvg_contractNumber, mvg_insuredId, mvg_ssn |
| **ORG** | — | Organisation | Other organizations | org_caseDate, org_caseId, org_contractNumber, org_insuredId |

**For complementary therapy (Tarif 590)**: Primarily VVG (supplementary). Some methods covered by KVG if therapist has special accreditation.

---

## 10. XML Export Format (Forum Datenaustausch)

The XSLT templates in iTherapeut_Data.fmp12 generate XML conforming to:

**Schema**: `generalInvoiceRequest_450.xsd`  
**Namespace**: `http://www.forum-datenaustausch.ch/invoice`  
**Standard**: Forum Datenaustausch (forum-datenaustausch.ch) — Swiss medical invoice XML

### 10.1 XML Structure

```xml
<invoice:request>
    <invoice:processing>           <!-- Processing instructions -->
    <invoice:payload>              <!-- Document type, copy, storno -->
        <invoice:credit>           <!-- Credit note reference -->
        <invoice:invoice>          <!-- Invoice metadata -->
            <invoice:request_id/>
            <invoice:request_date/>
            <invoice:request_timestamp/>
        <invoice:reminder>         <!-- Reminder level/text -->
        <invoice:body>             <!-- Main invoice body -->
            <invoice:prolog>       <!-- Software info -->
                <invoice:package>
                <invoice:generator>
            <invoice:remark/>      <!-- General remarks -->
            <invoice:balance>      <!-- Amount summary -->
                amount, amount_due, amount_obligations,
                amount_prepaid, amount_reminder, currency
            <invoice:esr9/>        <!-- Bank ESR -->
            <invoice:esrRed/>      <!-- Orange ESR/BVR -->
            <invoice:esrQR/>       <!-- QR-Rechnung -->
            <invoice:vat>          <!-- VAT summary -->
                <invoice:vat_rate/>
            <invoice:tiers_garant> <!-- OR tiers_payant -->
                <invoice:biller>   <!-- Billing entity -->
                <invoice:provider> <!-- Service provider -->
                <invoice:insurance><!-- Insurance company -->
                <invoice:patient>  <!-- Patient demographics -->
                <invoice:insured>  <!-- Insured person -->
                <invoice:guarantor><!-- Payment guarantor -->
                <invoice:referrer> <!-- Referring doctor -->
                <invoice:employer> <!-- Patient's employer -->
                <invoice:treatment><!-- Treatment context -->
                    canton, dateBegin, dateEnd, reason,
                    acid, apid
                <invoice:diagnosis><!-- Diagnosis info -->
                    type, code
                <invoice:kvg/><invoice:vvg/><invoice:uvg/>
                <invoice:ivg/><invoice:mvg/><invoice:org/>
                <invoice:services> <!-- Service line items -->
                    <invoice:service>
                        record_id, tariff_type="590",
                        code, ref_code, name,
                        date_begin, date_end, session,
                        quantity, amount, unit, unit_factor,
                        external_factor, obligation, vat_rate,
                        provider_id, responsible_id,
                        section_code, remark
                    <invoice:service_ex> <!-- Extended service -->
                <invoice:documents><!-- Attached documents -->
                    <invoice:document>
                        filename, mimeType, base64
            <invoice:transport>    <!-- Delivery info -->
                <invoice:via>
                    from, to, sequence_id
```

### 10.2 Key XML Attributes

| Attribute | Description | Example |
|-----------|-------------|---------|
| `tariff_type` | Tariff code | "590" |
| `zsr` | ZSR/RCC number | "A123456" |
| `ean_party` | GLN/EAN | "7601000000000" |
| `ssn` | AVS/AHV number | "756.1234.5678.90" |
| `uid_number` | UID | "CHE-123.456.789" |

---

## 11. Fibu (Finanzbuchhaltung / Accounting)

From Quick Start Guide (p.5): Available in PRO and PRAXIS versions.

### 11.1 Integration Points

- Each therapy method can have a **Haben-Konto** (credit account) for Fibu
- Each method can have a **MWST** (TVA/VAT) rate
- Invoice amounts automatically posted to configured accounts

### 11.2 Fibu Structure (from Fibu.fmp12)

The file is small (2.4 MB) — simple double-entry bookkeeping:
- **Kontenplan** (chart of accounts)
- **Buchungen** (journal entries) linked to invoices
- **Soll/Haben** (debit/credit) entries
- Print format: "1. Seite" (first page)

---

## 12. camt.054 Bank Integration

From Quick Start Guide (p.19):

- Download **camt.054** file from bank (ISO 20022 notification)
- Contains: `BkToCstmrDbtCdtNtfctn` → `Ntfctn` → `Ntry` → `NtryDtls` → `TxDtls`
- Fields extracted: `DbtrIBAN`, `IBAN`
- Auto-matches QR reference numbers to open invoices
- Marks matched invoices as paid

---

## 13. Digital Invoice Delivery

From Quick Start Guide (p.8, p.18):

- **iTherapeut Web** cloud platform for encrypted digital delivery
- Per-therapist "Sync" flag for cloud synchronization
- Per-patient delivery method: "digital" flag
- XML export to factoring partners (mediserv.ch)
- MediDoc integration for physio/ergotherapists

---

## 14. Mapping to iTherapeut 6.0

### 14.1 Already Implemented

| iTherapeut 5 | iTherapeut 6.0 | Status |
|-------------|----------------|--------|
| Adressen (Patient) | `patients` table + CRUD API | DONE (J1) |
| Therapeut (single) | `practitioners` table + CRUD API | DONE (post-sprint) |
| Sitzungen | `therapy_sessions` table + CRUD API | DONE (J1) |
| Rechnung | `invoices` table + CRUD API + PDF | DONE (J1) |
| QR-Rechnung | `POST /qrbill/generate` (SVG) | DONE (J1) |
| Tarif 590 / Rückforderungsbeleg | `POST /tarif590/generate` (PDF) | DONE (J2) |
| Barzahlung | Partial — status tracking exists | PARTIAL |
| Sequential numbering | ITH-YYYY-NNNN / T590-YYYY-NNNN | DONE (J1/J2) |
| Multi-praticien | `practitioners` with cabinet_id | DONE (post-sprint) |

### 14.2 Not Yet Implemented

| iTherapeut 5 | Priority | Complexity |
|-------------|----------|------------|
| **Mahnungen (reminders)** — reminder_level, escalation, surcharge | HIGH | Medium |
| **Serien (session series)** — group sessions by insurance type | HIGH | Medium |
| **Balance tracking** — amount_due, amount_prepaid, amount_reminder | HIGH | Low |
| **Barzahlung flow** — auto-create invoice + receipt + Rückforderungsbeleg | HIGH | Medium |
| **Insurance types** — KVG/VVG/UVG/IVG/MVG support | MEDIUM | High |
| **camt.054 import** — automated payment matching from bank | MEDIUM | Medium |
| **Provider vs Biller** — separate treating vs billing entity | MEDIUM | Low |
| **Referrer** — referring doctor tracking | LOW | Low |
| **XML export** — Forum Datenaustausch generalInvoice 4.5/5.0 | MEDIUM | High |
| **Tiers Payant** — direct insurance billing | LOW | Medium |
| **Storno/Gutschrift** — invoice cancellation/credit notes | MEDIUM | Low |
| **Rechnungslauf** — batch invoice run with sequential batch numbers | MEDIUM | Medium |
| **Fibu integration** — chart of accounts + journal entries | LOW | High |
| **Digital delivery** — encrypted invoice sending | LOW | High |
| **Employer/Guarantor** — for UVG/accident cases | LOW | Low |

### 14.3 Recommended Next Steps

1. **Add Mahnungen (reminders)** — Add `reminder_level`, `reminder_text`, `reminder_amount` to invoices; create `POST /invoices/{id}/remind` endpoint
2. **Add balance tracking** — Add `amount_due`, `amount_prepaid` computed fields to invoices
3. **Add Serien** — Create `session_series` table linking sessions by patient + insurance type
4. **Add Barzahlung flow** — Create `POST /invoices/cash-payment` that auto-creates invoice + marks paid + generates Rückforderungsbeleg
5. **Add insurance type support** — Add `insurance_law` enum (KVG/VVG/UVG/IVG/MVG) to sessions and invoices
6. **Add camt.054 import** — Create `POST /payments/import-camt054` for automated matching
7. **Add XML export** — Generate Forum Datenaustausch XML for digital transmission

---

## 15. Key Business Rules

1. **Rechnungsnummern never reused** — even cancelled invoices keep their number
2. **Barzahlung = 1 Rechnung + 1 Rückforderungsbeleg** — always paired
3. **ZSR number required** for barcode/QR generation on Rückforderungsbeleg
4. **PLZ + Geburtsdatum required** for barcode generation
5. **Tarif 590 = 5-minute units** — quantity is number of 5-min blocks
6. **Provider ≠ Biller** in multi-practitioner — biller is cabinet, provider is treating therapist
7. **Serien separate KVG/VVG** — same patient may have sessions under different insurance
8. **Mahnungen escalate** — Level 1 → 2 → 3 with increasing surcharges
9. **camt.054 matches by QR reference** — 27-digit reference number is key
10. **XML version 4.5.0** currently — v5.0 mandatory July 2027
