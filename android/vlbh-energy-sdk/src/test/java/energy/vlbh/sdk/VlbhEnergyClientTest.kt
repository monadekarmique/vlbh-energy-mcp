package energy.vlbh.sdk

import energy.vlbh.sdk.api.VlbhApiException
import energy.vlbh.sdk.api.VlbhEnergyClient
import energy.vlbh.sdk.models.SessionPullRequest
import energy.vlbh.sdk.models.SessionPushRequest
import kotlinx.coroutines.test.runTest
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class VlbhEnergyClientTest {

    private lateinit var server: MockWebServer
    private lateinit var client: VlbhEnergyClient

    @Before
    fun setUp() {
        server = MockWebServer()
        server.start()
        client = VlbhEnergyClient(
            baseUrl = server.url("/").toString().trimEnd('/'),
            token = "test-token"
        )
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun `pushSession sends correct headers and body`() = runTest {
        server.enqueue(
            MockResponse()
                .setBody("""{"success":true,"sessionKey":"K1","make_status":200}""")
                .addHeader("Content-Type", "application/json")
        )

        val resp = client.pushSession(
            SessionPushRequest(
                sessionKey = "K1",
                patientId = "P1",
                sessionNum = "1",
                programCode = "PROG",
                practitionerCode = "300"
            )
        )

        assertTrue(resp.success)

        val recorded = server.takeRequest()
        assertEquals("POST", recorded.method)
        assertEquals("/session/push", recorded.path)
        assertEquals("test-token", recorded.getHeader("X-VLBH-Token"))
        assertTrue(recorded.body.readUtf8().contains("\"sessionKey\":\"K1\""))
    }

    @Test
    fun `pullSession deserializes response`() = runTest {
        server.enqueue(
            MockResponse()
                .setBody("""{"session_key":"K1","patient_id":"P1","found":true,"timestamp":123}""")
                .addHeader("Content-Type", "application/json")
        )

        val resp = client.pullSession(SessionPullRequest(sessionKey = "K1"))
        assertEquals("K1", resp.sessionKey)
        assertTrue(resp.found)
    }

    @Test
    fun `health endpoint works without token`() = runTest {
        server.enqueue(
            MockResponse()
                .setBody("""{"status":"ok","service":"vlbh-energy-mcp","ts":1700000000}""")
                .addHeader("Content-Type", "application/json")
        )

        val resp = client.health()
        assertEquals("ok", resp.status)
    }

    @Test(expected = VlbhApiException::class)
    fun `401 throws VlbhApiException`() = runTest {
        server.enqueue(MockResponse().setResponseCode(401).setBody("""{"detail":"Unauthorized"}"""))
        client.pushSession(
            SessionPushRequest("K1", "P1", "1", "PROG", "300")
        )
    }
}
