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

export default {
	async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
		if (request.method !== "GET") {
			return new Response("Method Not Allowed", { status: 405 });
		}
		if (request.headers.get("X-MORPH-KEY") !== env.ROBOT_AUTH_KEY) {
			return new Response("Unauthorized", { status: 401 });
		}

		const cert = await env.morph.get("cert");
		const key = await env.morph.get("key");
		if (!cert || !key) {
			return new Response("Not Found", { status: 404 });
		}

		return new Response(JSON.stringify({ cert, key }), {
			headers: { "Content-Type": "application/json" },
		});
	}
} satisfies ExportedHandler<Env>;