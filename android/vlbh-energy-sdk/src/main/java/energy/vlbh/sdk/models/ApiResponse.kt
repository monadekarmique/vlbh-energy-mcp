package energy.vlbh.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PushResponse(
    val success: Boolean,
    val sessionKey: String? = null,
    val shamaneCode: String? = null,
    @SerialName("make_status") val makeStatus: Int? = null,
    val ok: Boolean? = null
)

@Serializable
data class HealthResponse(
    val status: String,
    val service: String,
    val ts: Long
)
