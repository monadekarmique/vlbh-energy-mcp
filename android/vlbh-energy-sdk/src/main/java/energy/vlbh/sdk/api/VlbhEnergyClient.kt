package energy.vlbh.sdk.api

import energy.vlbh.sdk.models.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit

class VlbhEnergyClient(
    private val baseUrl: String = "https://vlbh-energy-mcp.onrender.com",
    private val token: String,
    private val httpClient: OkHttpClient = defaultClient()
) {
    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
    }

    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    // ── Health ──────────────────────────────────────────────

    suspend fun health(): HealthResponse =
        get("/health")

    // ── Session ─────────────────────────────────────────────

    suspend fun pushSession(request: SessionPushRequest): PushResponse =
        post("/session/push", json.encodeToString(request))

    suspend fun pullSession(request: SessionPullRequest): SessionPullResponse =
        post("/session/pull", json.encodeToString(request))

    // ── Lead ────────────────────────────────────────────────

    suspend fun pushLead(request: LeadPushRequest): PushResponse =
        post("/lead/push", json.encodeToString(request))

    suspend fun pullLead(request: LeadPullRequest): LeadPullResponse =
        post("/lead/pull", json.encodeToString(request))

    // ── SLA ─────────────────────────────────────────────────

    suspend fun pushSla(request: SLAPushRequest): PushResponse =
        post("/sla/push", json.encodeToString(request))

    suspend fun pullSla(request: SLAPullRequest): SLAPullResponse =
        post("/sla/pull", json.encodeToString(request))

    // ── SLM ─────────────────────────────────────────────────

    suspend fun pushSlm(request: SLMPushRequest): PushResponse =
        post("/slm/push", json.encodeToString(request))

    suspend fun pullSlm(request: SLMPullRequest): SLMPullResponse =
        post("/slm/pull", json.encodeToString(request))

    // ── Tore ────────────────────────────────────────────────

    suspend fun pushTore(request: TorePushRequest): PushResponse =
        post("/tore/push", json.encodeToString(request))

    suspend fun pullTore(request: TorePullRequest): TorePullResponse =
        post("/tore/pull", json.encodeToString(request))

    // ── Internal ────────────────────────────────────────────

    private suspend inline fun <reified T> get(path: String): T = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("$baseUrl$path")
            .get()
            .build()

        val response = httpClient.newCall(request).execute()
        val body = response.body?.string() ?: throw VlbhApiException(response.code, "Empty response body")

        if (!response.isSuccessful) {
            throw VlbhApiException(response.code, body)
        }

        json.decodeFromString<T>(body)
    }

    private suspend inline fun <reified T> post(path: String, jsonBody: String): T =
        withContext(Dispatchers.IO) {
            val request = Request.Builder()
                .url("$baseUrl$path")
                .addHeader("X-VLBH-Token", token)
                .addHeader("Content-Type", "application/json")
                .post(jsonBody.toRequestBody(jsonMediaType))
                .build()

            val response = httpClient.newCall(request).execute()
            val body = response.body?.string() ?: throw VlbhApiException(response.code, "Empty response body")

            if (!response.isSuccessful) {
                throw VlbhApiException(response.code, body)
            }

            json.decodeFromString<T>(body)
        }

    companion object {
        fun defaultClient(): OkHttpClient = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }
}

class VlbhApiException(val statusCode: Int, message: String) : IOException("HTTP $statusCode: $message")
