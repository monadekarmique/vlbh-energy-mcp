package energy.vlbh.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ScoresLumiere(
    val sla: Int? = null,
    val slsa: Int? = null,
    val slsaS1: Int? = null,
    val slsaS2: Int? = null,
    val slsaS3: Int? = null,
    val slsaS4: Int? = null,
    val slsaS5: Int? = null,
    val slm: Int? = null,
    val totSlm: Int? = null
)

@Serializable
data class SLMPushRequest(
    val sessionKey: String,
    val scoresTherapist: ScoresLumiere,
    val scoresPatrick: ScoresLumiere,
    val therapistName: String? = null,
    val platform: String = "android"
)

@Serializable
data class SLMPullRequest(
    val sessionKey: String
)

@Serializable
data class SLMPullResponse(
    @SerialName("session_key") val sessionKey: String,
    val therapist: ScoresLumiere? = null,
    val patrick: ScoresLumiere? = null,
    val found: Boolean,
    val timestamp: Long? = null
)
