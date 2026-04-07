package energy.vlbh.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class LeadPushRequest(
    val shamaneCode: String,
    val prenom: String,
    val nom: String? = null,
    val tier: String = "CERTIFIEE",
    val status: String = "ACTIVE",
    val sessionKey: String? = null,
    val platform: String = "android"
)

@Serializable
data class LeadPullRequest(
    val shamaneCode: String
)

@Serializable
data class LeadPullResponse(
    @SerialName("shamane_code") val shamaneCode: String,
    val prenom: String? = null,
    val nom: String? = null,
    val tier: String? = null,
    val status: String? = null,
    @SerialName("session_key") val sessionKey: String? = null,
    val found: Boolean,
    val timestamp: Long? = null
)
