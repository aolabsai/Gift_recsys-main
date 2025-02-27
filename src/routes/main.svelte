<script>
    let email = "";

    import { onMount } from "svelte";


      
    const baseEndpoint = "https://gift-recsys.onrender.com"; // Change to http://127.0.0.1:5000 for local testing and https://gift-recsys.onrender.com for production
    // const baseEndpoint = "http://127.0.0.1:5000";
    // const baseEndpoint = "https://aolabsgiftrec-backend-equal-strawberry-s3o2.zeet-aolabsai-hc.zeet.app";

    // will be used for changing url for development and production without manually changing the url
    // const baseEndpoint = import.meta.env.VITE_BACKEND_URL;

    let countries = [];
    let selectedCountry = "US";
    let age = 18;
    let gender = [];
    let budget = 50;
    let giftCategories = [];
    let recommendationScore = null;
    let product = null;
    let NextProduct = null;
    let genre = null;
    let target = null;
    let occasion = null;
    let extraInfo = null;

    let token = localStorage.getItem('token');

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

    let stopButtonClicked = false;

    async function fetchCountries() {
        const response = await fetch("/google-countries.json");
        countries = await response.json();
    }

    async function findGifts() {
        console.log("getting gift cats")
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
        console.log("finished")
    }

    async function getProductfromGift() {
        console.log("start get product")
        const searchTerm = giftCategories[Math.floor(Math.random() * giftCategories.length)];
        const productResponse = await fetch(`${baseEndpoint}/get_product`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: searchTerm, budget, agentInUse }),
        });
        NextProduct = await productResponse.json();
        console.log("finished to get product", NextProduct)
    }


    async function getRecommendation() {
        product = NextProduct
        isLoading = true;
        console.log("using product: ", product)
        const data = {product, agentInUse };
        const agentResponse = await fetch(`${baseEndpoint}/agent-recommend`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        
        const agentData = await agentResponse.json();
        console.log("agentdata:", agentData);
        recommendationScore = agentData.recommendation_score;
        target = agentData.target;
        genre = agentData.genre;
        link = product.link;
        if (agentData.recommendation_score <recommendation_threshold) { 
            console.log("Recommendation score is less than threshold, getting another recommendation");
            recommendation_threshold -= 20; // bring down threshold
            if (!stopButtonClicked) {
                findGifts();
                getProductfromGift();
                product = NextProduct
                await getRecommendation();

                
            }else{
                stopButtonClicked = false
            }
            number_of_products_skipped += 1;
        } else {
            console.log(
                "Recommendation score is greater than threshold, showing recommendation",
            );
            recommendation_threshold = 50; // reset threshold
            number_of_products_skipped = 0 

        }
        console.log("ended")
        isLoading = false;
        console.log("Number of products skipped: ", number_of_products_skipped);
        console.log("Recommendation threshold: ", recommendation_threshold);
        findGifts();    // load the next gift categories 
        getProductfromGift();
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

        savedProducts = res["products"];
    }

    async function check_login()  {
        const params = new URLSearchParams(window.location.search);
        token = params.get("token")

        if (token)  {
            const response = await fetch(`${baseEndpoint}/check_login`, {
            method: "GET",
            headers: { "Content-Type": "application/json" , "Authorization": token},

        });

            if (response.status == 200) {
                const data = await response.json();
                console.log("data: ", data)
                email = data.email
                loggedin = true;
                getAgents();
                
            }

        }
    }

    // Google OAuth Login function
    async function loginWithGoogle() {
        try {
            const response = await fetch(`${baseEndpoint}/login_with_google`, {method: "POST",});
            const data = await response.json();
            if (response.status === 200) {
                window.location.href = data.url; //redirect to google 
            } else {
                alert("Login failed!");
            }
        } catch (error) {
            console.error("Error during Google login:", error);
        }
    }

        
    

    function updateAgentInUse(email, name) {
        agentInUse = [email, name];
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
    onMount(async () => {
  check_login();
});


    onMount(fetchCountries);
</script>

<main>
    {#if !loggedin}
        <div id="login">

            <h1 id="top">Effortless Gift Shopping</h1>
            <h1 id="header">Find the perfect gift in less than five clicks</h1>
            <p id="subheader">AI-powered shopping companion for
                efficient, stress-free gift shoopping.</p>
            <img
                id="start_page_img"
                alt="start_page_img"
                src="start_page_img.png"
            />
            <button on:click={loginWithGoogle}>Sign in with Google</button>
            <p>----or----</p>
            <input type="email" bind:value={email} placeholder="Email" />
            <input type="password" bind:value={password} placeholder="Password"/>

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
        <p>Hey there, awesome gifter! 🎉
            I'm so pumped you're here! As you probably already know, the AO Labs team put together this app to help YOU become the ultimate gift-giving legend. Below, you can start setting up profiles for all the people you're picking out giftsfor. Go ahead and create as many profiles you need — no limits here! I personally recommend one for every special person in your life, but just between us, I may or may not have made a profile for myself too... 😏  After all, a litle self-love never hurt anyone, right? So, dive oin and have a blast creating the perfect gifts for everyone (and maybe a little something for you too)! Happy gifting! 🎁 </p>
        <div id="create_agent_page">
            <h1 id="grey_small_header">Create a new profile</h1>

            
            <label>Who are you looking to buy something for? <input placeholder="Name" type="text" bind:value={newAgentName}></label>

            <label>Where do they live?:
                <select bind:value={selectedCountry}>
                    {#each countries as country}
                        <option value={country.country_code}
                            >{country.country_name}</option
                        >
                    {/each}
                </select>
            </label>
            <label>How old are they?: <input type="number" bind:value={age} min="0" max="100" /></label>
            <label>What gender are they?:
                <select bind:value={gender}>
                    <option>Male</option>
                    <option>Female</option>
                    <option>Non-binary</option>
                    <option>Prefer not to say</option>
                </select>
            </label>
            <label>Now get creative, if you were to introduce me, what would you say?: <input type="text" bind:value={extraInfo} /></label>

            <button id="main_button" on:click={() => { createNewAgent(); }}>Create</button>
            <h1 id="grey_small_header">Saved profiles</h1>
            <p>All the profiles that you've created will be stored here. Don't worry! You can also make me forget some going inside each profile and click on 'Delete Profile'.</p>
        </div>
    {/if}
    {#if agents.length > 0 && !createNewAgentPage && !showrecommendationPage && loggedin}
        <div class="agent-list">
            {#each agents as agent}
                <div class="select_agents">
                    <img
                        id="agent_img"
                        alt="agent_img"
                        src="agent_img.jpeg"
                    />
                    <h1>{agent.name}</h1>
                    <p>{agent.age}, {agent.gender}, {agent.country}</p>
                    <button on:click={async () => { 
                        showrecommendationPage = true;
                        isLoading = true
                        await updateAgentInUse(agent.email, agent.name);   // Update agent in use
                        await getProduct();   // Find saved products
                        await findGifts();    // Find gift search terms
                        await getProductfromGift();   // Get random gift
                        await getRecommendation();    // Get agent recommendations
                        isLoading = false
                    }}>
                        Select
                    </button>
                </div>
            {/each}
        </div>
    {/if}<!--
    {#if createNewAgentPage}

    {/if}-->

    <div id="recommendation_page">
        <div id="recommendation_page_left"></div>
        {#if showrecommendationPage && loggedin}

        <button on:click={() => { 
            showrecommendationPage=false;
            deleteAgent();
        }}>Delete Profile</button>
        <h1>Finding the perfect gift for: {agentInUse[1]}</h1>
        <h4>What's the budget?</h4>
        <input type="range" min="10" max="1000" step="5" bind:value="{budget}"/>
        <span>{budget}$</span>
        <label>What's the occasion you're planning on giving something<input type="text" placeholder="Is it a birthday or anniversary?" bind:value={occasion}></label>
        <label>What is the season? (I don't want to recommend a swimming suit in winter!)
            <select bind:value={season}>
                <option>Winter</option>
                <option>Spring</option>
                <option>Summer</option>
                <option>Fall</option>
        </label>


        {/if}

        {#if isLoading}
            <div class="spinner-container">
                {#if isLoading&&showrecommendationPage}
                    <p> We're looking for the perfect gift!</p>
                    <button id="main_button" on:click={() =>  {
                        stopButtonClicked = true
                    }
                        }>I like this gift</button>
                {/if}

                <div class="spinner"></div>
            </div>
        {/if}

        {#if product&&showrecommendationPage}
        
            <h2>Recommended Product</h2>
            <img src={product.photo} alt={product.name} id="recommend_product_img" />
            <p>Name: {product.name}</p>
            <p>Price: {product.price}</p>

            <a id="buy_now_link" href={link} target="_blank">Buy Now </a>
            <button id="save_button" on:click={saveProduct} >Save for later</button>
            
            <p>Recommendation Score: {recommendationScore}%</p>

            <button id="main_button" on:click={trainAgentPos}>Recommend More Products Like This</button>
            <button id="main_button" on:click={trainAgentNeg}>Recommend Less Products Like This</button>
        
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