package energy.vlbh.sdk

import energy.vlbh.sdk.models.*
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.Assert.*
import org.junit.Test

class ModelsSerializationTest {

    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
    }

    @Test
    fun `SessionPushRequest serializes with camelCase`() {
        val req = SessionPushRequest(
            sessionKey = "00-12-002-0301",
            patientId = "P001",
            sessionNum = "1",
            programCode = "PROG1",
            practitionerCode = "300"
        )
        val encoded = json.encodeToString(req)
        assertTrue(encoded.contains("\"sessionKey\""))
        assertTrue(encoded.contains("\"platform\":\"android\""))
    }

    @Test
    fun `SessionPullResponse deserializes snake_case`() {
        val body = """
            {"session_key":"00-12-002-0301","patient_id":"P001","found":true,"timestamp":1700000000}
        """.trimIndent()
        val resp = json.decodeFromString<SessionPullResponse>(body)
        assertEquals("00-12-002-0301", resp.sessionKey)
        assertEquals("P001", resp.patientId)
        assertTrue(resp.found)
    }

    @Test
    fun `LeadPushRequest defaults`() {
        val req = LeadPushRequest(shamaneCode = "300", prenom = "Cornelia")
        val encoded = json.encodeToString(req)
        assertTrue(encoded.contains("\"tier\":\"CERTIFIEE\""))
        assertTrue(encoded.contains("\"status\":\"ACTIVE\""))
        assertTrue(encoded.contains("\"platform\":\"android\""))
    }

    @Test
    fun `SLMPullResponse deserializes nested ScoresLumiere`() {
        val body = """
            {
                "session_key": "K1",
                "therapist": {"sla": 200, "slm": 50000, "totSlm": 500},
                "patrick": {"sla": 180},
                "found": true,
                "timestamp": null
            }
        """.trimIndent()
        val resp = json.decodeFromString<SLMPullResponse>(body)
        assertTrue(resp.found)
        assertEquals(200, resp.therapist?.sla)
        assertEquals(50000, resp.therapist?.slm)
        assertEquals(180, resp.patrick?.sla)
    }

    @Test
    fun `TorePullResponse deserializes full stockage`() {
        val body = """
            {
                "session_key": "T1",
                "stockage": {
                    "tore": {"intensite": 5000, "phase": "CHARGE"},
                    "glycemie": {"index": 120, "balance": 80},
                    "sclerose": {"score": 200},
                    "couplage": {
                        "correlationTG": 45,
                        "phaseCouplage": "SYNERGIQUE",
                        "scleroseTissulaire": {"fibroseIndex": 300, "zonesAtteintes": 5}
                    },
                    "niveau": 7000,
                    "capacite": 10000,
                    "rendement": 70.0
                },
                "found": true,
                "timestamp": 1700000000
            }
        """.trimIndent()
        val resp = json.decodeFromString<TorePullResponse>(body)
        assertTrue(resp.found)
        assertEquals(5000, resp.stockage?.tore?.intensite)
        assertEquals("CHARGE", resp.stockage?.tore?.phase)
        assertEquals(45, resp.stockage?.couplage?.correlationTG)
        assertEquals(300, resp.stockage?.couplage?.scleroseTissulaire?.fibroseIndex)
        assertEquals(70.0, resp.stockage?.rendement!!, 0.01)
    }

    @Test
    fun `TorePushRequest serializes correctly`() {
        val req = TorePushRequest(
            sessionKey = "T1",
            stockage = StockageEnergetique(
                tore = ChampToroidal(intensite = 5000, phase = "EQUILIBRE"),
                niveau = 8000,
                capacite = 10000
            ),
            therapistName = "Cornelia"
        )
        val encoded = json.encodeToString(req)
        assertTrue(encoded.contains("\"intensite\":5000"))
        assertTrue(encoded.contains("\"phase\":\"EQUILIBRE\""))
        assertTrue(encoded.contains("\"therapistName\":\"Cornelia\""))
    }

    @Test
    fun `PushResponse deserializes`() {
        val body = """{"success":true,"sessionKey":"K1","make_status":200}"""
        val resp = json.decodeFromString<PushResponse>(body)
        assertTrue(resp.success)
        assertEquals(200, resp.makeStatus)
    }
}
