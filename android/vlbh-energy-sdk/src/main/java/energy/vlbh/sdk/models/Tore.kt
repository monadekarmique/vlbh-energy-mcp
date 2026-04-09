package energy.vlbh.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ChampToroidal(
    val intensite: Int? = null,
    val coherence: Int? = null,
    val frequence: Double? = null,
    val phase: String? = null // REPOS, CHARGE, DECHARGE, EQUILIBRE
)

@Serializable
data class Glycemie(
    val index: Int? = null,
    val balance: Int? = null,
    val absorption: Int? = null,
    val resistanceScore: Int? = null
)

@Serializable
data class Sclerose(
    val score: Int? = null,
    val densite: Int? = null,
    val elasticite: Int? = null,
    val permeabilite: Int? = null
)

@Serializable
data class ScleroseTissulaire(
    val fibroseIndex: Int? = null,
    val zonesAtteintes: Int? = null,
    val profondeur: Int? = null,
    val revascularisation: Int? = null,
    val decompaction: Int? = null
)

@Serializable
data class CouplageToreGlycemie(
    val correlationTG: Int? = null,
    val correlationTS: Int? = null,
    val correlationGS: Int? = null,
    val scoreCouplage: Int? = null,
    val fluxNet: Int? = null,
    val phaseCouplage: String? = null, // SYNERGIQUE, ANTAGONISTE, NEUTRE, TRANSITOIRE
    val scleroseTissulaire: ScleroseTissulaire? = null
)

@Serializable
data class StockageEnergetique(
    val tore: ChampToroidal? = null,
    val glycemie: Glycemie? = null,
    val sclerose: Sclerose? = null,
    val couplage: CouplageToreGlycemie? = null,
    val niveau: Int? = null,
    val capacite: Int? = null,
    val tauxRestauration: Int? = null,
    val rendement: Double? = null
)

@Serializable
data class TorePushRequest(
    val sessionKey: String,
    val stockage: StockageEnergetique,
    val therapistName: String? = null,
    val platform: String = "android"
)

@Serializable
data class TorePullRequest(
    val sessionKey: String
)

@Serializable
data class TorePullResponse(
    @SerialName("session_key") val sessionKey: String?,
    val stockage: StockageEnergetique? = null,
    val found: Boolean,
    val timestamp: Long? = null
)
