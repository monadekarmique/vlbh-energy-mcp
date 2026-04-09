package energy.vlbh.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class SessionPushRequest(
    val sessionKey: String,
    val patientId: String,
    val sessionNum: String,
    val programCode: String,
    val practitionerCode: String,
    val therapistName: String? = null,
    val status: String = "ACTIVE",
    val eventCount: Int = 0,
    val liberatedCount: Int = 0,
    val platform: String = "android"
)

@Serializable
data class SessionPullRequest(
    val sessionKey: String
)

@Serializable
data class SessionPullResponse(
    @SerialName("session_key") val sessionKey: String,
    @SerialName("patient_id") val patientId: String? = null,
    @SerialName("session_num") val sessionNum: String? = null,
    @SerialName("program_code") val programCode: String? = null,
    @SerialName("practitioner_code") val practitionerCode: String? = null,
    @SerialName("therapist_name") val therapistName: String? = null,
    val status: String? = null,
    @SerialName("event_count") val eventCount: Int? = null,
    @SerialName("liberated_count") val liberatedCount: Int? = null,
    val found: Boolean,
    val timestamp: Long? = null
)
