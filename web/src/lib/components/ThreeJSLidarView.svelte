<script lang="ts">
    import type { OccupancyGrid } from "$lib/foxglove/types/occupancy-grid.js";
	import type { PoseWithCovariance } from "$lib/foxglove/types/pose.js";
    import { getRobotConnectionContext } from "$lib/robot-connection.svelte.js";
    import { onMount, untrack } from "svelte";
	import * as THREE from "three";
	
	let container: HTMLDivElement | undefined = $state();
	let renderer: THREE.WebGLRenderer | undefined;
	let camera: THREE.PerspectiveCamera | undefined;
	let scene: THREE.Scene;
	let lidarPoints: THREE.BufferGeometry;
	let poseMarker: THREE.Mesh | undefined;
	let poseArrow: THREE.ArrowHelper | undefined;
	let navigationCursorMarker: THREE.Mesh | undefined;
	let navigationTargetMarker: THREE.Mesh | undefined;
	let navigationArrow: THREE.ArrowHelper | undefined;
	let robotPosition = $state({ x: 0, y: 0, z: 0 });
	let navigationMode = $state<"idle" | "select-target" | "select-heading">("idle");
	let navigationTarget = $state<{ x: number; y: number } | null>(null);
	let navigationHeading = $state<number | null>(null);
	let navigationCursor = $state<{ x: number; y: number } | null>(null);

	const NAV_ARROW_LENGTH = 0.9;
	const NAV_ARROW_HEAD_LENGTH = 0.24;
	const NAV_ARROW_HEAD_WIDTH = 0.14;

	const pickRaycaster = new THREE.Raycaster();
	const pickMouse = new THREE.Vector2();
	const mapPlane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
	const mapHitPoint = new THREE.Vector3();

	let robotConnection = getRobotConnectionContext();

	const startNavigation = () => {
		navigationMode = "select-target";
		navigationTarget = null;
		navigationHeading = null;
		navigationCursor = null;
	};

	const cancelNavigation = () => {
		navigationMode = "idle";
		navigationTarget = null;
		navigationHeading = null;
		navigationCursor = null;
	};

	const onLidarPointerDown = (event: PointerEvent) => {
		if (!container || !camera || event.button !== 0) return;

		if (navigationMode === "idle") return;

		const bounds = container.getBoundingClientRect();
		if (bounds.width === 0 || bounds.height === 0) return;

		pickMouse.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
		pickMouse.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;

		pickRaycaster.setFromCamera(pickMouse, camera);
		const intersection = pickRaycaster.ray.intersectPlane(mapPlane, mapHitPoint);
		if (!intersection) return;

		if (navigationMode === "select-target") {
			navigationTarget = {
				x: intersection.x,
				y: intersection.y,
			};
			navigationMode = "select-heading";
			return;
		}

		if (navigationMode === "select-heading" && navigationTarget) {
			const heading = Math.atan2(
				intersection.y - navigationTarget.y,
				intersection.x - navigationTarget.x,
			);
			navigationHeading = heading;
			console.log(
				`Navigate to (${navigationTarget.x.toFixed(3)}, ${navigationTarget.y.toFixed(3)}) heading ${heading.toFixed(3)} rad`,
			);
			navigationMode = "idle";
			navigationTarget = null;
			return;
		}
	};

	const onLidarPointerMove = (event: PointerEvent) => {
		if (!container || !camera) return;
		if (navigationMode === "idle") {
			navigationCursor = null;
			return;
		}

		const bounds = container.getBoundingClientRect();
		if (bounds.width === 0 || bounds.height === 0) return;

		pickMouse.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
		pickMouse.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;

		pickRaycaster.setFromCamera(pickMouse, camera);
		const intersection = pickRaycaster.ray.intersectPlane(mapPlane, mapHitPoint);
		if (!intersection) return;

		navigationCursor = {
			x: intersection.x,
			y: intersection.y,
		};
	};

	// Initialize Three.js scene and renderer on mount.
	onMount(() => {
		renderer = new THREE.WebGLRenderer({ antialias: true });
		scene = new THREE.Scene();
		camera = new THREE.PerspectiveCamera(
			75,
			container ? container.clientWidth / container.clientHeight : 1,
			0.1,
			1000,
		);
		camera.position.z = 10;

		lidarPoints = new THREE.BufferGeometry();
		const lidarPointMaterial = new THREE.PointsMaterial({ color: 0xffffff, size: 0.1, sizeAttenuation: true });
		const points = new THREE.Points(lidarPoints, lidarPointMaterial);
		scene.add(points);

		const markerGeometry = new THREE.SphereGeometry(0.16, 16, 16);
		const markerMaterial = new THREE.MeshBasicMaterial({ color: 0x22c55e });
		poseMarker = new THREE.Mesh(markerGeometry, markerMaterial);
		scene.add(poseMarker);

		poseArrow = new THREE.ArrowHelper(
			new THREE.Vector3(1, 0, 0),
			new THREE.Vector3(0, 0, 0),
			0.9,
			0x22c55e,
			0.24,
			0.14,
		);
		scene.add(poseArrow);

		const navigationMarkerGeometry = new THREE.SphereGeometry(0.12, 16, 16);
		const navigationMarkerMaterial = new THREE.MeshBasicMaterial({ color: 0x10b981 });
		navigationCursorMarker = new THREE.Mesh(
			navigationMarkerGeometry,
			navigationMarkerMaterial,
		);
		navigationCursorMarker.visible = false;
		scene.add(navigationCursorMarker);

		navigationTargetMarker = new THREE.Mesh(
			navigationMarkerGeometry,
			navigationMarkerMaterial,
		);
		navigationTargetMarker.visible = false;
		scene.add(navigationTargetMarker);

		navigationArrow = new THREE.ArrowHelper(
			new THREE.Vector3(1, 0, 0),
			new THREE.Vector3(0, 0, 0),
			NAV_ARROW_LENGTH,
			0x10b981,
			NAV_ARROW_HEAD_LENGTH,
			NAV_ARROW_HEAD_WIDTH,
		);
		navigationArrow.visible = false;
		scene.add(navigationArrow);

		return () => {
			if (renderer) {
				renderer.dispose();
				lidarPoints.dispose();
				lidarPointMaterial.dispose();
				if (poseMarker) {
					poseMarker.geometry.dispose();
					(poseMarker.material as THREE.Material).dispose();
				}
				if (navigationCursorMarker) {
					navigationCursorMarker.geometry.dispose();
					(navigationCursorMarker.material as THREE.Material).dispose();
				}
				if (navigationTargetMarker) {
					navigationTargetMarker.geometry.dispose();
					(navigationTargetMarker.material as THREE.Material).dispose();
				}
				camera = undefined;
				renderer = undefined;
				poseMarker = undefined;
				poseArrow = undefined;
				navigationCursorMarker = undefined;
				navigationTargetMarker = undefined;
				navigationArrow = undefined;
			}
		}
	});

	const updateNavigationVisuals = () => {
		if (!navigationCursorMarker || !navigationTargetMarker || !navigationArrow) return;

		navigationCursorMarker.visible = false;
		navigationTargetMarker.visible = false;
		navigationArrow.visible = false;

		if (navigationMode === "select-target" && navigationCursor) {
			navigationCursorMarker.visible = true;
			navigationCursorMarker.position.set(navigationCursor.x, navigationCursor.y, 0.05);
			return;
		}

		if (navigationMode === "select-heading" && navigationTarget) {
			navigationTargetMarker.visible = true;
			navigationTargetMarker.position.set(navigationTarget.x, navigationTarget.y, 0.05);
			if (navigationCursor) {
				navigationCursorMarker.visible = true;
				navigationCursorMarker.position.set(navigationCursor.x, navigationCursor.y, 0.05);

				const direction = new THREE.Vector3(
					navigationCursor.x - navigationTarget.x,
					navigationCursor.y - navigationTarget.y,
					0,
				).normalize();
				if (Number.isFinite(direction.x) && Number.isFinite(direction.y)) {
					navigationArrow.visible = true;
					navigationArrow.position.set(navigationTarget.x, navigationTarget.y, 0.05);
					navigationArrow.setDirection(direction);
					navigationArrow.setLength(
						NAV_ARROW_LENGTH,
						NAV_ARROW_HEAD_LENGTH,
						NAV_ARROW_HEAD_WIDTH,
					);
				}
			}
		}
	};

	$effect(() => {
		updateNavigationVisuals();
	});

	// Bind renderer to container.
	$effect(() => {
		if (!container) return;

		if (!renderer || !camera) return;
		container.appendChild(renderer.domElement);

		const onResize = () => {
			if (!container || !renderer || !camera) return;
			
			const bounds = container.getBoundingClientRect();
			const width = bounds.width;
			const height = bounds.height;
			if (width === 0 || height === 0) return;

			renderer.setSize(width, height, false);
			renderer.setViewport(0, 0, width, height);
			camera.aspect = width / height;
			camera.updateProjectionMatrix();
		};
		onResize();

		const resizeObserver = new ResizeObserver(onResize);
		resizeObserver.observe(container);

		let animationFrameId: number | undefined;
		const animate = () => {
			animationFrameId = requestAnimationFrame(animate);
			if (renderer && camera) {
				renderer.render(scene, camera);
			}
		};
		animate();

		return () => {
			resizeObserver.disconnect();
			if (animationFrameId) {
				cancelAnimationFrame(animationFrameId);
			}
			container?.removeChild(renderer?.domElement as HTMLCanvasElement);
		};
	});

	$effect(() => {
		if (!robotConnection.client || robotConnection.status !== "connected") return;
		const client = robotConnection.client;

		const onMapData = (grid: OccupancyGrid) => {
			const points = Array.from(grid.data)
			.map((value, index) => ({ value, index }))
			.filter(({ value }) => value > 0) // Filter out unknown and free cells
			.map(({ index }) => {
				// OccupancyGrid data is row-major, left->right and bottom->top from origin.
				const x = (index % grid.width) * grid.resolution + grid.origin.x;
				const y = Math.floor(index / grid.width) * grid.resolution + grid.origin.y;
				return [x, y, 0];
			});

			const flattenedPoints = new Float32Array(points.flat());
			lidarPoints.setAttribute('position', new THREE.BufferAttribute(flattenedPoints, 3));
			lidarPoints.attributes.position.needsUpdate = true;
		}

		const onPoseData = (pose: PoseWithCovariance) => {
			if (!poseMarker || !poseArrow) return;

			const position = pose.pose.position;
			const orientation = pose.pose.orientation;
			robotPosition = {
				x: position.x,
				y: position.y,
				z: position.z,
			};

			poseMarker.position.set(position.x, position.y, position.z);
			poseArrow.position.set(position.x, position.y, position.z);

			const quat = new THREE.Quaternion(
				orientation.x,
				orientation.y,
				orientation.z,
				orientation.w,
			);
			const direction = new THREE.Vector3(1, 0, 0).applyQuaternion(quat).normalize();
			poseArrow.setDirection(direction);

			if (camera) {
				camera.position.x = position.x;
				camera.position.y = position.y;
				camera.lookAt(position.x, position.y, 0);
			}
		}

		client.addCallback("map", onMapData);
		client.addCallback("pose", onPoseData);

		return () => {
			client?.removeCallback("map", onMapData);
			client?.removeCallback("pose", onPoseData);
			untrack(() => {
				if (lidarPoints) {
					lidarPoints.dispose();
				}
			});
		}
	});
	
</script>

<div
	class="relative flex-1 min-h-0 w-full"
	bind:this={container}
	role="application"
	aria-label="Lidar view"
	onpointerdown={onLidarPointerDown}
	onpointermove={onLidarPointerMove}
>
	<div class="absolute top-8 left-8">
		<div class="p-6 rounded-3xl bg-white/10 backdrop-blur-md border border-white/20 shadow-2xl pointer-events-auto">
			<div class="text-xs uppercase tracking-[0.16em] text-white/70">Robot Position</div>
			<div class="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm text-white/90">
				<span class="font-semibold">X</span>
				<span>{robotPosition.x.toFixed(3)}</span>
				<span class="font-semibold">Y</span>
				<span>{robotPosition.y.toFixed(3)}</span>
			</div>

			<div class="mt-4 flex items-center gap-2">
				<button
					type="button"
					class="px-4 py-2 rounded-xl text-sm font-semibold transition"
					style:background="var(--accent)"
					style:color="var(--page-bg)"
					disabled={navigationMode !== "idle"}
					onclick={startNavigation}
				>
					Navigate
				</button>
				{#if navigationMode !== "idle"}
					<button
						type="button"
						class="px-3 py-2 rounded-xl border border-white/25 bg-white/10 text-white/90 hover:bg-white/20 transition"
						onclick={cancelNavigation}
					>
						Cancel
					</button>
				{/if}
			</div>

			{#if navigationMode === "select-target"}
				<p class="mt-3 text-xs text-white/75">Click a target position in the map.</p>
			{:else if navigationMode === "select-heading" && navigationTarget}
				<p class="mt-3 text-xs text-white/75">
					Now click the direction the robot should face.
				</p>
			{/if}
		</div>
	</div>

</div>
