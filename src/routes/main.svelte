<script>
    import { onMount } from "svelte";
    let countries = [];
    let selectedCountry = "US";
    let age = 18;
    let gender = [];
    let budget = 50;
    let giftCategories = [];
    let recommendedProduct = null;
    let recommendationScore = null;
    let product = null;
    let genre = null;

    let loggedin = false
    let email = ""
    let password = ""

    async function fetchCountries() {
        const response = await fetch('/public/google-countries.json');
        countries = await response.json();
    }

    async function findGifts() {
        const response = await fetch("http://127.0.0.1:5000/get-gift-categories", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ age, gender, budget }),
        });
        const data = await response.json();
        giftCategories = data.categories;
    }

    async function getRecommendation() {
        findGifts()
        const searchTerm = giftCategories[Math.floor(Math.random() * giftCategories.length)];
        const productResponse = await fetch("http://127.0.0.1:5000/get-product", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: searchTerm, budget }),
        });
        product = await productResponse.json();
        console.log(product)
        recommendedProduct = product;

        const agentResponse = await fetch("http://127.0.0.1:5000/agent-recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(product),
        });
        const agentData = await agentResponse.json();
        console.log("agentdata:, ",  agentData)
        recommendationScore = agentData.recommendation_score;
        genre = agentData.genre;
    }

    async function trainAgentPos() {
        const Label = [1,1,1,1,1,1,1,1,1,1]
        const data = { product, Label };
        console.log("data:", data)
        const response1 = await fetch("http://127.0.0.1:5000/trainAgent", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const response = await response1.json;
        console.log(response) 
        getRecommendation()
    }


    async function  trainAgentNeg() {
        const Label = [0,0,0,0,0,0,0,0,0,0]
        const data = { product, Label };
        const response1 = await fetch("http://127.0.0.1:5000/trainAgent", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const response = await response1.json;
        console.log(response) 
        getRecommendation()
    }

    async function login() {
        const data = {email, password}
        const response = await fetch("http://127.0.0.1:5000/login", {
            method:"POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (response.status === 200) {
        loggedin = true;
    }


        
    }
    onMount(fetchCountries);
</script>

<main>
    {#if !loggedin}
        <h1>Log In</h1>
        <label>Email: <input type="email" bind:value={email}></label>
        <label>Password: <input type="text" bind:value={password}></label>
        <button on:click={login}>Continue</button>
    {/if}
    {#if loggedin}
    <h1>Gift Recommender</h1>
    <label>Country:
        <select bind:value={selectedCountry}>
            {#each countries as country}
                <option value={country.country_code}>{country.country_name}</option>
            {/each}
        </select>
    </label>
    <label>Age: <input type="number" bind:value={age} min="0" max="100" /></label>
    <label>Gender:
        <select bind:value={gender}>
            <option>Male</option>
            <option>Female</option>
            <option>Non-binary</option>
            <option>Prefer not to say</option>
        </select>
    </label>
    <h4>Budget</h4>
    <input type="range" min="10" max="1000" step="5" bind:value="{budget}"/>
    <span>{budget}$</span>
    <button on:click={getRecommendation}>Get Recommendation</button>
    {/if}

    {#if recommendedProduct}
        <h2>Recommended Product</h2>
        <p>Name: {recommendedProduct.name}</p>
        <p>Price: {recommendedProduct.price}</p>
        <p>Genre: {genre}</p>
        <img src={recommendedProduct.photo} alt={recommendedProduct.name} />
        <p>Recommendation Score: {recommendationScore}%</p>

        <button on:click={trainAgentPos}>Recommend More</button>
        <button on:click={trainAgentNeg}>Recommend Less</button>
    {/if}
</main>
