<script>
    let email = "";
    import { onMount } from "svelte";

    onMount(() => {
        // Check the URL for the email if user used google auth to sign in
        const urlParams = new URLSearchParams(window.location.search);
        email = urlParams.get("email");
        if (email) {
            console.log("Logged in as", email);
            login_user(email);
        }
    });
    // import {backend_url} from '$env/static/private';

    // console.log(import.meta.env.BACKEND_URL);
    console.log(import.meta.env.VITE_BACKEND_URL);
    // const baseEndpoint = "http://127.0.0.1:5000";
    // const baseEndpoint = import.meta.env.VITE_BACKEND_URL;
    // const baseEndpoint = "https://giftrec.aolabs.ai";
    const baseEndpoint = "https://gift-recsys.onrender.com"
    // const baseEndpoint = "aolabsgiftrec-backend-equal-straw-f0736f.782df154-c4c7-43e7-9965-fa00212de798.svc.cluster.local"; // Change to http://127.0.0.1:5000 for local testing and https://gift-recsys.onrender.com for production

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

    let password = "";
    let message = "";
    let isLoading = false;
    let showrecommendationPage = false;
    let agents = [];
    let agentInUse = null;
    let link = null;
    let season = null;
    let savedProducts = [];

    let number_of_products_skipped = 0;
    let recommendation_threshold = 50; // active threshold system

    function login_user(email) {
        loggedin = true; // Set loggedin to true as you are now logged in
        console.log("Logged in as", email);
        getAgents(); // Now you can fetch the agents after the email is set
    }

    async function fetchCountries() {
        const response = await fetch("/google-countries.json");
        countries = await response.json();
    }

    async function findGifts() {
        let data_to_send = {
            agentInUse: agentInUse,
            budget: budget,
            occasion: occasion,
            season: season,
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

        const searchTerm =
            giftCategories[Math.floor(Math.random() * giftCategories.length)];
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
        if (agentData.recommendation_score < recommendation_threshold) {
            console.log(
                "Recommendation score is less than threshold, getting another recommendation",
            );
            recommendation_threshold -= 20; // bring down threshold
            getRecommendation();
            number_of_products_skipped += 1;
        } else {
            console.log(
                "Recommendation score is greater than threshold, showing recommendation",
            );
            recommendation_threshold = 50; // reset threshold
        }
        console.log("Number of products skipped: ", number_of_products_skipped);
        console.log("Recommendation threshold: ", recommendation_threshold);
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
        const data = {
            email,
            newAgentName,
            selectedCountry,
            age,
            gender,
            extraInfo,
        };

        const response = await fetch(`${baseEndpoint}/createNewAgent`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const res = await response.json();
        console.log(res);
        getAgents();
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
        console.log("email: ", email);
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

    async function saveProduct() {
        const data = { product, agentInUse };
        const response = await fetch(`${baseEndpoint}/saveProduct`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const res = await response.json();
        console.log(res);
        getProduct();
    }

    async function getProduct() {
        const data = { product, agentInUse };
        const response = await fetch(`${baseEndpoint}/getProducts`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const res = await response.json();
        console.log(res);

        savedProducts = res["products"];
    }

    async function login_with_google() {
        try {
            const response = await fetch(`${baseEndpoint}/login_with_google`);
            const data = await response.json();

            if (response.status === 200) {
                // redirect the user to the Google OAuth page
                console.log("Redirecting to Google OAuth URL:", data.url);
                window.location.href = data.url; // redirects the user to Google login page
            } else {
                message = data.error || "Failed to get Google OAuth URL";
            }
        } catch (error) {
            message =
                error.message || "An error occurred during authentication";
        }
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
            <img
                id="start_page_img"
                alt="start_page_img"
                src="https://s3-alpha-sig.figma.com/img/6be8/76b1/a59b0193952b1c07665ec0ef5458555a?Expires=1739145600&Key-Pair-Id=APKAQ4GOSFWCVNEHN3O4&Signature=a~WBMZovxZB0Sc1UUxuNdTn3sjklDGreg043~LKVo-9y17PIz2N~wrHeQX0jIBPb7988ebJ8ANk6ZWpuqYYEMiUkBTjdmakVRSF6AoyHykjyVjX0kx38VMZAu-2QFkvAX4G5IKOGagnC~pXKnfsdCp9JBxoANEb2mZE5Cut8aelKu~Y8ojo2l9uC4FEl3TdMjfBXy4qEYg5fWdRZ1ZHWYLcvo1-WYJCmmvBZsjjQ9xtO11zKl-euHxuXrKh2ugla2OsrbLmuvOneizuJv7g1lQdNcGlTIdx6Z9uuh9hTiXLptTNbuxg27IUDQi4OXn8L8EjkoslCmdN7pB8dSmIE7w__"
            />
            <h1 id="rainbow_header">Delightful gift giving starts here</h1>
            <button on:click={login_with_google}>Sign in with Google</button>
            <p>----or----</p>
            <label>Email: <input type="email" bind:value={email} /></label>
            <label
                >Password: <input
                    type="password"
                    bind:value={password}
                /></label
            >
            <button
                id="main_button"
                on:click={() => {
                    login();
                    getAgents();
                }}>Continue</button
            >
            <p>----or----</p>
            <button id="main_button" on:click={createAccount}
                >Create New Account</button
            >
            <p>{message}</p>
        </div>
    {/if}
    {#if loggedin}
        <div id="nav">
            <button
                id="nav_button"
                on:click={() => {
                    showrecommendationPage = false;
                    createNewAgentPage = false;
                    getAgents();
                }}>Home</button
            >
            <button
                id="nav_button"
                on:click={() => {
                    loggedin = false;
                    email = "";
                    password = "";
                    message = "";
                }}>Logout</button
            >
        </div>
    {/if}
    {#if loggedin && !showrecommendationPage && !createNewAgentPage}
        <div id="header_text">
            <h1 id="rainbow_header">Hello, {email}.</h1>
        </div>

        <div id="create_agent_page">
            <h1 id="grey_small_header">Create a new agent</h1>

            <label
                >Name <input
                    placeholder="Agent Name"
                    type="text"
                    bind:value={newAgentName}
                /></label
            >

            <label
                >Country:
                <select bind:value={selectedCountry}>
                    {#each countries as country}
                        <option value={country.country_code}
                            >{country.country_name}</option
                        >
                    {/each}
                </select>
            </label>
            <label
                >Age: <input
                    type="number"
                    bind:value={age}
                    min="0"
                    max="100"
                /></label
            >
            <label
                >Gender:
                <select bind:value={gender}>
                    <option>Male</option>
                    <option>Female</option>
                    <option>Non-binary</option>
                    <option>Prefer not to say</option>
                </select>
            </label>
            <label
                >Extra Info: <input type="text" bind:value={extraInfo} /></label
            >

            <button
                id="main_button"
                on:click={() => {
                    createNewAgent();
                }}>Create</button
            >
            <h1 id="grey_small_header">Or Continue Where You Left Off</h1>
        </div>
    {/if}
    {#if agents.length > 0 && !createNewAgentPage && !showrecommendationPage && loggedin}
        <div class="agent-list">
            {#each agents as agent}
                <div class="select_agents">
                    <img
                        id="agent_img"
                        alt="agent_img"
                        src="https://s3-alpha-sig.figma.com/img/b6cf/c50b/674d6137a02d8c5b27b14be520e715b4?Expires=1739145600&Key-Pair-Id=APKAQ4GOSFWCVNEHN3O4&Signature=PAK5hDpRsD4q1U4b~~qyMS3ktrCt6fhjl6HDWuK6ZqDfsvniATLDs0JseBmUNNX9u2yAHxL8HZxvm~BHVIoRxAI4Bf8GLEnyMKY~w~O6wSBiiFqlRAew8u2irOJ5e-v8aI6ki4m5Pv48Wo0bCAxRjYMDlRt5O60k7V1LC5B1kwga3Vh~H5yC2-Ei4MVnSv3ULJoVe8-WV~X3zhTbGouGJd4023FxB~-K28h9t14ItPywTipFkN~9X45t9cZ7ACMHcWs~iyCHW7gx46FQZvH~YUUH8eHDttf0HLHiTm3-DFS3fzP63Mt8yaXcE-or4825ztRr2QAXAmTky1tpO41WZg__"
                    />
                    <h1>{agent.name}</h1>
                    <p>{agent.age}, {agent.gender}, {agent.country}</p>
                    <button
                        on:click={() => {
                            showrecommendationPage = true;
                            updateAgentInUse(agent.email, agent.name);
                            getProduct();
                            getRecommendation();
                        }}>Select</button
                    >
                </div>
            {/each}
        </div>
    {/if}<!--
    {#if createNewAgentPage}

    {/if}-->

    <div id="recommendation_page">
        <div id="recommendation_page_left"></div>
        {#if showrecommendationPage && loggedin}
            <button
                on:click={() => {
                    showrecommendationPage = false;
                    deleteAgent();
                }}>Delete Agent</button
            >
            <h1>Finding the perfect gift for: {agentInUse}</h1>
            <h4>Budget</h4>
            <input
                type="range"
                min="10"
                max="1000"
                step="5"
                bind:value={budget}
            />
            <span>{budget}$</span>
            <input type="text" placeholder="Occasion" bind:value={occasion} />
            <label
                >Season
                <select bind:value={season}>
                    <option>Winter</option>
                    <option>Spring</option>
                    <option>Summer</option>
                    <option>Fall</option>
                </select></label
            >
        {/if}

        {#if isLoading}
            <div class="spinner-container">
                <div class="spinner"></div>
            </div>
        {/if}

        {#if recommendedProduct && showrecommendationPage}
            <h2>Recommended Product</h2>
            <img
                src={recommendedProduct.photo}
                alt={recommendedProduct.name}
                id="recommend_product_img"
            />
            <p>Name: {recommendedProduct.name}</p>
            <p>Price: {recommendedProduct.price}</p>
            <p>Genre: {genre}</p>
            <p>Target: {target}</p>

            <div>
                <a id="buy_now_link" href={link} target="_blank">Buy Now </a>
            </div>
            <button id="save_button" on:click={saveProduct}
                >Save for later</button
            >

            <p>Recommendation Score: {recommendationScore}%</p>

            <button id="main_button" on:click={trainAgentPos}
                >Recommend More</button
            >
            <button id="main_button" on:click={trainAgentNeg}
                >Recommend Less</button
            >
        {/if}

        {#if showrecommendationPage && loggedin}
            <h1>Your saved products</h1>

            <div id="savedProducts">
                {#each savedProducts as product}
                    <div class="savedProduct">
                        <p>{product.name}</p>
                        <a id="buy_now_link" href={product.link} target="_blank"
                            >Buy Now
                        </a>
                        <div id="divider_between_saved_products"></div>
                    </div>
                {/each}
            </div>
        {/if}
    </div>
</main>
