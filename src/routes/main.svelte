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

    let createNewAgentPage = false;
    let newAgentName = "";

    let loggedin = false;
    let email = "";
    let password = "";
    let message = '';
    let isLoading = false;
    let showrecommendationPage = false;
    let agents = [];
    let agentInUse = null

    async function fetchCountries() {
        const response = await fetch('/google-countries.json');
        countries = await response.json();
    }

    async function findGifts() {
        const response = await fetch("https://gift-recsys.onrender.com/get-gift-categories", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ age, gender, budget }),
        });
        const data = await response.json();
        giftCategories = data.categories;
    }

    async function getRecommendation() {
        findGifts();
        isLoading = true
        const searchTerm = giftCategories[Math.floor(Math.random() * giftCategories.length)];
        const productResponse = await fetch("https://gift-recsys.onrender.com/get-product", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: searchTerm, budget }),
        });
        product = await productResponse.json();
        recommendedProduct = product;
        
        const data = {product, agentInUse}
        console.log("calling agent recommend")
        const agentResponse = await fetch("http://127.0.0.1:5000/agent-recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        isLoading = false
        const agentData = await agentResponse.json();
        console.log("agentdata:", agentData);
        recommendationScore = agentData.recommendation_score;
        genre = agentData.genre;
    }

    async function trainAgentPos() {
        const Label = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1];
        const data = { product, Label, agentInUse};
        const response1 = await fetch("https://gift-recsys.onrender.com/trainAgent", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const response = await response1.json();
        console.log(response);
        getRecommendation();
    }

    async function trainAgentNeg() {
        const Label = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        const data = { product, Label, agentInUse};
        const response1 = await fetch("https://gift-recsys.onrender.com/trainAgent", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const response = await response1.json();
        console.log(response);
        getRecommendation();
    }

    async function createNewAgent(){
        const data = {email, newAgentName}
        
        const response = await fetch("https://gift-recsys.onrender.com/createNewAgent", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const res = await response.json()
        console.log(res)
    }

    async function getAgents(){
        const data = {email}
        isLoading = true
        const response = await fetch("https://gift-recsys.onrender.com/getAgents", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const res = await response.json()
        isLoading = false
        console.log(res)
        agents = res;
    }

    function updateAgentInUse(email, name){

        agentInUse = [email, name]
        console.log("Agent is use: ", agentInUse)
    }

    const createAccount = async () => {
    if (password.length < 6) {
    message = "Password must be at least 6 characters long";
    return;
  }
    isLoading = true
    try {
      const response = await fetch("https://gift-recsys.onrender.com/createAccount", {
        method: "POST",  
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),  
      });
      const data = await response.json();
      isLoading = false
      message = data.message;
    } catch (error) {
      isLoading = false;
      message = error.response.data.error;
    }
  };

  const login = async () => {
    isLoading = true;
    try {
        const response = await fetch("https://gift-recsys.onrender.com/login", {
            method: "POST",  
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),  
        });
        const data = await response.json();
        message = data.message;
        if (response.status==200)
            {loggedin = true;}  
        
    } catch (error) {
        message = error.message || "An error occurred"; 
    } finally {
        isLoading = false;  
    }
};



    onMount(fetchCountries);
</script>


<main>
    {#if !loggedin}
        <h1>Log In</h1>
        <label>Email: <input type="email" bind:value={email}></label>
        <label>Password: <input type="text" bind:value={password}></label>
        <button on:click={login}>Continue</button>
        <button on:click={createAccount}>Create New Account</button>
        <p>{message}</p>
    {/if}
    {#if loggedin && !showrecommendationPage && !createNewAgentPage}

        <h1>Hello</h1>
        <button on:click={() => { 
            createNewAgentPage = true;
        }}>Create a New Agent</button>
        <button on:click={getAgents}>Retrieve Agents</button>

    {/if}
    {#if agents.length > 0}
        <h2>Choose an Agent</h2>
        <div class="agent-list">
            {#each agents as agent}
                <div class="select_agents">
                    <button on:click={() => { 
                        showrecommendationPage = true;
                        updateAgentInUse(agent.email, agent.name)
                    }}>{agent.name}</button>
                </div>
            {/each}
        </div>
    {/if}
    {#if createNewAgentPage}
    <button on:click={() => { 
        createNewAgentPage = false;
        showrecommendationPage = false;

    }}>Back</button>
        <h1>Create a new agent</h1>
        <input placeholder="Agent Name" bind:value={newAgentName}>
        <button on:click={createNewAgent}>Create</button>
    {/if}
    {#if showrecommendationPage}
    <button on:click={() => { 
        showrecommendationPage = false;
    }}>Back</button>
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

    {#if recommendedProduct&&showrecommendationPage}
        <h2>Recommended Product</h2>
        <p>Name: {recommendedProduct.name}</p>
        <p>Price: {recommendedProduct.price}</p>
        <p>Genre: {genre}</p>
        <img src={recommendedProduct.photo} alt={recommendedProduct.name} />
        <p>Recommendation Score: {recommendationScore}%</p>

        <button on:click={trainAgentPos}>Recommend More</button>
        <button on:click={trainAgentNeg}>Recommend Less</button>
    {/if}
    {#if isLoading}
    <div class="spinner"></div>
    <p id="loading_text">Loading, this could take 1-2 minutes</p>
  {/if}
</main>
