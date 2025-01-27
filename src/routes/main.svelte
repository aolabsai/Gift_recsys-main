<script>
    import { onMount } from "svelte";

    const baseEndpoint = "https://gift-recsys.onrender.com"; // Change to http://127.0.0.1:5000 for local testing and https://gift-recsys.onrender.com for production

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
    let target = null;
    let occasion = null;
    let extraInfo = null;

    let createNewAgentPage = false;
    let newAgentName = "";

    let loggedin = false;
    let email = "";
    let password = "";
    let message = '';
    let isLoading = false;
    let showrecommendationPage = false;
    let agents = [];
    let agentInUse = null;
    let link = null;
    let season = null;

    async function fetchCountries() {
        const response = await fetch('/google-countries.json');
        countries = await response.json();
    }

    async function findGifts() {
        let data_to_send = {
            "agentInUse": agentInUse,
            "budget": budget,
            "occasion": occasion,
            "season": season
        };
        const response = await fetch(`${baseEndpoint}/get-gift-categories`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data_to_send }),
        });
        const data = await response.json();
        giftCategories = data.categories;
    }

    async function getRecommendation() {
        findGifts();
        isLoading = true;

        const searchTerm = giftCategories[Math.floor(Math.random() * giftCategories.length)];
        const productResponse = await fetch(`${baseEndpoint}/get-product`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: searchTerm, budget, agentInUse }),
        });
        product = await productResponse.json();
        recommendedProduct = product;
        console.log("", recommendedProduct);

        const data = { product, agentInUse };
        console.log("calling agent recommend");
        const agentResponse = await fetch(`${baseEndpoint}/agent-recommend`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        isLoading = false;
        const agentData = await agentResponse.json();
        console.log("agentdata:", agentData);
        recommendationScore = agentData.recommendation_score;
        target = agentData.target;
        genre = agentData.genre;
        link = recommendedProduct.link;
    }

    async function trainAgentPos() {
        const Label = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1];
        const data = { product, Label, agentInUse };
        const response1 = await fetch(`${baseEndpoint}/trainAgent`, {
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
        const data = { product, Label, agentInUse };
        const response1 = await fetch(`${baseEndpoint}/trainAgent`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const response = await response1.json();
        console.log(response);
        getRecommendation();
    }

    async function createNewAgent() {
        console.log(selectedCountry);
        const data = { email, newAgentName, selectedCountry, age, gender, extraInfo };

        const response = await fetch(`${baseEndpoint}/createNewAgent`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const res = await response.json();
        console.log(res);
    }

    async function deleteAgent() {
        console.log(selectedCountry);
        const data = { agentInUse };

        const response = await fetch(`${baseEndpoint}/deleteAgent`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const res = await response.json();
        console.log(res);
    }

    async function getAgents() {
        const data = { email };
        isLoading = true;
        const response = await fetch(`${baseEndpoint}/getAgents`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const res = await response.json();
        isLoading = false;
        console.log(res);
        agents = res;
    }

    function updateAgentInUse(email, name) {
        agentInUse = [email, name];
        console.log("Agent is use: ", agentInUse);
    }

    const createAccount = async () => {
        if (password.length < 6) {
            message = "Password must be at least 6 characters long";
            return;
        }
        isLoading = true;
        try {
            const response = await fetch(`${baseEndpoint}/createAccount`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const data = await response.json();
            isLoading = false;
            message = data.message;
        } catch (error) {
            isLoading = false;
            message = error.response.data.error;
        }
    };

    const login = async () => {
        isLoading = true;
        try {
            const response = await fetch(`${baseEndpoint}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const data = await response.json();
            message = data.message;
            if (response.status == 200) {
                loggedin = true;
            }
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
    <div id="login">
        <h1>Log In</h1>
        <img id="start_page_img" src="https://s3-alpha-sig.figma.com/img/6be8/76b1/a59b0193952b1c07665ec0ef5458555a?Expires=1739145600&Key-Pair-Id=APKAQ4GOSFWCVNEHN3O4&Signature=a~WBMZovxZB0Sc1UUxuNdTn3sjklDGreg043~LKVo-9y17PIz2N~wrHeQX0jIBPb7988ebJ8ANk6ZWpuqYYEMiUkBTjdmakVRSF6AoyHykjyVjX0kx38VMZAu-2QFkvAX4G5IKOGagnC~pXKnfsdCp9JBxoANEb2mZE5Cut8aelKu~Y8ojo2l9uC4FEl3TdMjfBXy4qEYg5fWdRZ1ZHWYLcvo1-WYJCmmvBZsjjQ9xtO11zKl-euHxuXrKh2ugla2OsrbLmuvOneizuJv7g1lQdNcGlTIdx6Z9uuh9hTiXLptTNbuxg27IUDQi4OXn8L8EjkoslCmdN7pB8dSmIE7w__">
        
       
            <label>Email: <input type="email" bind:value={email}></label>
            <label>Password: <input type="text" bind:value={password}></label>
            <button on:click={() => { login(); getAgents(); }}>Continue</button>
            <button on:click={createAccount}>Create New Account</button>
            <p>{message}</p>
        </div>

    {/if}
    {#if loggedin && !showrecommendationPage && !createNewAgentPage}
        <div id="header_text">
            <h1 id="rainbow_header">Hello, {email}.</h1>
            <h1>Who are you shopping for today?</h1>
        </div>
        <!---
        <button on:click={() => { 
            createNewAgentPage = true;
        }}>Create a New Shopping Agent</button>
        <button on:click={getAgents}>Retrieve Agents</button>
-->
        <button on:click={getAgents}>Retrieve Agents</button>
        <div id="create_agent_page">
            <h1>Create a new agent</h1>

            
            <input placeholder="Agent Name" bind:value={newAgentName}>

            <button on:click={() => { createNewAgent(); getAgents(); }}>Create</button>
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
            <label>Extra Info: <input type="text" bind:value={extraInfo} /></label>
            <p>{message}</p>
        </div>


    {/if}
    {#if (agents.length > 0) && !createNewAgentPage && !showrecommendationPage}
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
    {/if}<!--
    {#if createNewAgentPage}

    {/if}-->
    {#if showrecommendationPage}
    <button on:click={() => { 
        showrecommendationPage = false;
    }}>Back</button>
    <button on:click={deleteAgent}>Delete Agent</button>
    <h1>Finding the perfect gift for: {agentInUse}</h1>
    <h4>Budget</h4>
    <input type="range" min="10" max="1000" step="5" bind:value="{budget}"/>
    <span>{budget}$</span>
    <input type="text" placeholder="Occasion" bind:value={occasion}>
    <label>season
        <select bind:value={season}>
            <option>Winter</option>
            <option>Spring</option>
            <option>Summer</option>
            <option>Fall</option>
    </label>
    <button on:click={getRecommendation}>Get Recommendation</button>
    {/if}

    {#if recommendedProduct&&showrecommendationPage}
        <h2>Recommended Product</h2>
        <p>Name: {recommendedProduct.name}</p>
        <p>Price: {recommendedProduct.price}</p>
        <p>Genre: {genre}</p>
        <p>Target: {target}</p>
        <a href={link}>Buy Now</a>
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
