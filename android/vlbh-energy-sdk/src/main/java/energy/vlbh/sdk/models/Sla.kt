package energy.vlbh.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class SLAPushRequest(
    val sessionKey: String,
    val slaTherapist: Int? = null,
    val slaPatrick: Int? = null,
    val therapistName: String? = null,
    val platform: String = "android"
)

@Serializable
data class SLAPullRequest(
    val sessionKey: String
)

@Serializable
data class SLAPullResponse(
    @SerialName("session_key") val sessionKey: String,
    @SerialName("sla_therapist") val slaTherapist: Int? = null,
    @SerialName("sla_patrick") val slaPatrick: Int? = null,
    val found: Boolean,
    val timestamp: Long? = null
)
