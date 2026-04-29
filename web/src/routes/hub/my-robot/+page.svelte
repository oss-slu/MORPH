<script lang="ts">
	import { goto } from "$app/navigation";
	import ConnectView from "$lib/components/ConnectView.svelte";
	import ThreeJSLidarView from "$lib/components/ThreeJSLidarView.svelte";
	import WASDController from "$lib/components/WASDController.svelte";
	import { getRobotConnectionContext } from "$lib/robot-connection.svelte";

	const robotConnection = getRobotConnectionContext();

	function disconnect() {
		robotConnection.disconnect();
	}
</script>

<svelte:head>
	<title>Live Control Hub | MORPH</title>
	<meta
		name="description"
		content="Live MORPH robot connection status and available robot topics."
	/>
</svelte:head>

{#if robotConnection.status !== "connected"}
	<ConnectView />
{:else}
	<div class="w-full h-full min-h-0 flex flex-col flex-1">
		<ThreeJSLidarView />
		
		<div class="absolute bottom-8 right-8 flex flex-col gap-4 items-end pointer-events-none">
			<div class="p-6 rounded-3xl bg-white/10 backdrop-blur-md border border-white/20 shadow-2xl pointer-events-auto">
				<WASDController />
			</div>
		</div>
	</div>
{/if}
