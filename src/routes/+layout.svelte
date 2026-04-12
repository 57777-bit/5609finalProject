

<script>
	let { children } = $props();
</script>

{@render children()}

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
		background-color: #f8f9fa;
	}
</style>
