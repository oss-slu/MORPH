/**
 * Welcome to Cloudflare Workers! This is your first worker.
 *
 * - Run `npm run dev` in your terminal to start a development server
 * - Open a browser tab at http://localhost:8787/ to see your worker in action
 * - Run `npm run deploy` to publish your worker
 *
 * Bind resources to your worker in `wrangler.jsonc`. After adding bindings, a type definition for the
 * `Env` object can be regenerated with `npm run cf-typegen`.
 *
 * Learn more at https://developers.cloudflare.com/workers/
 */

interface RequestBody {
	robot_id: string;
	ip: string;
}

export default {
	async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
		if (request.method !== "POST") {
			return new Response("Method Not Allowed", { status: 405 });
		}
		if (request.headers.get("X-MORPH-KEY") !== env.ROBOT_AUTH_KEY) {
			return new Response("Unauthorized", { status: 401 });
		}

		try {
			const { robot_id, ip } = await request.json() as RequestBody;
			const recordName = `${robot_id}.robot.76500000.xyz`;

			const baseUrl = `https://api.cloudflare.com/client/v4/zones/${env.ZONE_ID}/dns_records`;

			// 1. Check if the record already exists
			const listResp = await fetch(`${baseUrl}?name=${recordName}`, {
				headers: { Authorization: `Bearer ${env.CF_API_TOKEN}` }
			});
			const listData: any = await listResp.json();
			const existingRecord = listData.result?.[0];

			// 2. Prepare the payload
			const payload = {
				type: "A",
				name: recordName,
				content: ip,
				ttl: 60,      // Fast propagation
				proxied: false // MUST be false for private/local IPs
			};

			// 3. Update (PUT) or Create (POST)
			const finalUrl = existingRecord ? `${baseUrl}/${existingRecord.id}` : baseUrl;
			const method = existingRecord ? "PUT" : "POST";

			const updateResp = await fetch(finalUrl, {
				method: method,
				headers: {
					"Authorization": `Bearer ${env.CF_API_TOKEN}`,
					"Content-Type": "application/json"
				},
				body: JSON.stringify(payload)
			});

			if (!updateResp.ok) {
				const errorMsg = await updateResp.text();
				return new Response(`Cloudflare API Error: ${errorMsg}`, { status: 500 });
			}

			return new Response(`DNS Updated: ${recordName} -> ${ip}`, { status: 200 });
		} catch (err: any) {
			return new Response(`Error processing request: ${err.message}`, { status: 400 });
		}
	},
} satisfies ExportedHandler<Env>;
