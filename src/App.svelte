<script>
  import Rounter from "svelte-spa-router"
  import main from "./routes/main.svelte"





//test
  let routes = {
    "/":  main,

  }
</script>

<main>
  <Rounter {routes}/>
</main>




