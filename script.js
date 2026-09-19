/* =====================================================
   ELEMENTS
===================================================== */

// Find the user input box from HTML
// and store it in the input variable
const input = document.getElementById("user-input");

// Find the Send button from HTML
// and store it in the sendBtn variable
const sendBtn = document.getElementById("send-btn");

// Find the area where messages will be displayed
const chatArea = document.getElementById("chat-area");

// Find the New Chat button
const newChatBtn = document.getElementById("new-chat-btn");

// Find the Home button
const homeBtn = document.getElementById("home-btn");

// Find the Find Standards button
const standardsBtn = document.getElementById("standards-btn");

// Find the Certification Guide button
const certificationBtn = document.getElementById("certification-btn");

// Find the Laboratory Finder button
const laboratoryBtn = document.getElementById("laboratory-btn");

// Find the Settings button
const settingsBtn = document.getElementById("settings-btn");

// Find the Recent Chats container
const recentChats = document.getElementById("recent-chats");

// Find the place where standards will be displayed
const standardsPanel = document.getElementById("standards-panel");

// Find the place where certification will be displayed
const certificationPanel = document.getElementById("certification-panel");

// Find the place where sources will be displayed
const sourcesPanel = document.getElementById("sources-panel");

//for collapse of the sidebar
const collapseBtn = document.getElementById("collapse-btn");
const sidebar = document.querySelector(".sidebar");


// Store the backend URL in one variable
const API_URL = "https://bis-smartassist-backend.onrender.com/api/chat";


/* =====================================================
   CHAT HISTORY
===================================================== */

// Create a variable called chatHistory
// let is used because the value can change later

let chatHistory =
    JSON.parse(  // convert JSON text into a JavaScript value that JavaScript can actually use.

        // Get the saved chat history from browser storage
        localStorage.getItem("bisSaarthiHistory")

    ) || []; // || means or

// If there is no saved history,
// use an empty array


/* =====================================================
   SAVE HISTORY
===================================================== */

// This function saves chat history in browser storage

function saveHistory() {

    // setItem means save something in localStorage

    localStorage.setItem(

        // This is the key/name used to store the data
        "bisSaarthiHistory",

        // Convert chatHistory into a string by using stringify
        // so it can be stored in localStorage
        JSON.stringify(chatHistory)

    );

}


/* =====================================================
   BACKEND FUNCTION
===================================================== */

// This function sends a message to the backend

async function askBackend(message) {

    // fetch() sends a request to the backend
    // await means wait until the backend gives a response

    const response =
        await fetch(
            API_URL,
            {
                // POST means we are sending data
                // to the backend
                method: "POST",

                // Tell the backend that
                // we are sending JSON data
                headers: {
                    "Content-Type":
                        "application/json"
                },

                // Convert our JavaScript object
                // into JSON string
                body:
                    JSON.stringify({

                        // Send the message to backend
                        message:
                            message

                    })
            }
        );


    // Get the data sent by the backend
    // and convert it from JSON into JavaScript data

    const data =
        await response.json();


    // Check if backend returned an error

    if (!response.ok) {

        throw new Error(
            data.detail ||
            "Backend request failed"
        );

    }


    // Return the backend data
    return data;

}


/* =====================================================
   GET ANSWER
===================================================== */

// This function gets the answer from backend data

function getAnswer(
    data,
    fallback
) {

    // First check data.response
    // If it doesn't exist, check data.answer
    // If neither exists, use the fallback

    return (
        data.response ||
        data.answer ||
        fallback
    );

}


/* =====================================================
   UPDATE RECENT CHATS
===================================================== */

function updateRecentChats() {

    // Clear the currently displayed recent chats
    recentChats.innerHTML = "";


    // Take the last 5 chats
    // and reverse them so newest appears first

    const recent =
        chatHistory
            .slice(-5)
            .reverse();


    // Go through each chat one by one

    recent.forEach(function (chat) {

        // Create a new div element

        const item =
            document.createElement("div");


        // Add the recent-chat CSS class

        item.classList.add(
            "recent-chat"
        );


        // Put the question inside the div(variable item)

        item.textContent =
            chat.question;


        // Show the question when the user hovers over it

        item.title =
            chat.question;


        // When this recent chat is clicked,
        // display the saved chat

        item.addEventListener(
            "click",
            function () {

                displaySavedChat(chat);

            }
        );


        // Add the new div inside Recent Chats

        recentChats.appendChild(item);

    });

}


/* =====================================================
   DISPLAY SAVED CHAT
===================================================== */

// This function displays a previously saved chat
// chat contains the saved question and answer

function displaySavedChat(chat) {

    // Clear the current chat area

    chatArea.innerHTML = "";


    /* USER MESSAGE */

    // Create a div for the saved user question

    const userMessage =
        document.createElement("div");


    // Give the div the user-message CSS class

    userMessage.classList.add(
        "user-message"
    );


    // Put the saved question inside the div

    userMessage.textContent =
        chat.question;


    // Add the user message inside chatArea

    chatArea.appendChild(
        userMessage
    );


    /* AI MESSAGE */

    // Create a div for the AI answer

    const result =
        document.createElement("div");


    // Give it the bot-message CSS class

    result.classList.add(
        "bot-message"
    );


    // Create an empty variable
    // where we will build the HTML

    let html = "";


    // Check if the saved chat has an answer

    if (chat.answer) {

        // Add the answer HTML to html

        html += `

            <div class="answer">

                ${
                    // Convert Markdown answer into HTML
                    marked.parse(chat.answer)
                }

            </div>

        `;

    }


    /* CONFIDENCE */

    // Check if confidence exists

    if (
        chat.confidence !== undefined
    ) {

        // Create confidence HTML automatically
        // and add it to html

        html +=
            createConfidenceHTML(
                chat.confidence
            );

    }


    /* SOURCES */

    // Check that sources exist
    // AND that there is at least one source

    if (
        chat.sources &&
        chat.sources.length > 0
    ) {

        // Create source HTML
        // and add it to html

        html +=
            createSourcesHTML(
                chat.sources
            );

    }


    /* ACTION BUTTONS */

    // Add Copy, Like and Dislike buttons

    // copyAnswer is the function

    html += createActionButtonsHTML();


    // Put the complete HTML inside the result div

    result.innerHTML =
        html;


    // Add the AI result inside chatArea

    chatArea.appendChild(
        result
    );


    // Update the right-side panel

    updateRightPanel(
        chat
    );


    // Scroll to the bottom of the chat

    scrollToBottom();

}


/* =====================================================
   CONFIDENCE
===================================================== */

// This function creates the HTML
// for showing the confidence value

function createConfidenceHTML(
    confidence  // confidence is the input for the function
) {

    // Convert confidence into a number

    let value =
        Number(confidence);


    // If backend gives confidence like 0.85,
    // convert it into 85

    if (value <= 1) {

        value =
            value * 100;

    }


    // Round the number

    value =
        Math.round(value);


    // Keep the value between 0 and 100

    value =
        Math.max(  //.max will chose the maximum number
            0,
            Math.min( //.min will chose the minimum number
                100,
                value
            )
        );


    // Start with Low confidence

    let label =
        "Low";


    // If value is 75 or more,
    // change label to High

    if (value >= 75) {

        label =
            "High";

    }


    // If value is 50 or more,
    // change label to Medium

    else if (value >= 50) {

        label =
            "Medium";

    }


    // Return the HTML for confidence display
    //return will send the value back to the function, when the function is called createConfidenceHTML()
    //${label} and ${value} are JavaScript values inserted into the HTML.
    //style="width: ${value}%" this will fill the value% of the bar(jitna % value hoga)

    return `

        <div class="confidence-box">

            <div class="confidence-header">

                <span class="confidence-label">

                    🟢 Confidence

                </span>


                <span class="confidence-value">

                    ${label} · ${value}%

                </span>

            </div>


            <div class="confidence-bar">

                <div
                    class="confidence-fill"
                    style="width: ${value}%"
                ></div>

            </div>

        </div>

    `;

}


/* =====================================================
   SOURCES
===================================================== */

// This function creates the HTML
// for displaying sources

function createSourcesHTML(
    sources
) {

    // Start with the Sources heading

    let html = `

        <div class="sources-title">

            📚 Sources

        </div>

    `;


    // Go through every source one by one

    sources.forEach(
        function (source) {

            // Get source title
            // If title does not exist, use name
            // If neither exists, use BIS Document

            const name =
                source.title ||  // || means or, this will try to get the title
                source.name ||   // || means or, this will try to get the name
                "BIS Document";  // if got nothing then use bis document


            // Get the clause number
            // If it does not exist, use empty string

            const clause =
                source.clause ||
                "";


            // Get the page number
            // If it does not exist, use empty string

            const page =
                source.page ||
                "";


            // Get the source URL
            // If it does not exist, use source_url
            // If neither exists, use "#"

            const url =
                source.url ||
                source.source_url ||
                "#";


            // Add this source to the HTML

            html += `

                <div class="source-item">

                    <a
                        class="source-name"
                        href="${url}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >

                        ${name}

                    </a>


                    <div class="source-details">

                        ${
                            clause
                                ? `Clause ${clause}`  // this is a short if else if there is clause then show if not then empty string
                                : ""
                        }

                        ${
                            clause && page
                                ? " • "   // show • only when clause and page both exist
                                : ""
                        }

                        ${
                            page
                                ? `Page ${page}`  // short if else
                                : ""
                        }

                    </div>

                </div>

            `;

        }
    );


    // Return the complete source HTML

    return html;

}


/* =====================================================
   ACTION BUTTONS
===================================================== */

// This function creates the action buttons

function createActionButtonsHTML() {

    // Add Copy, Like and Dislike buttons

    return `

        <div class="message-actions">

            <button
                class="message-action"
                onclick="copyAnswer(this)"
            >

                📋 Copy

            </button>


            <button
                class="message-action"
            >

                👍

            </button>


            <button
                class="message-action"
            >

                👎

            </button>

        </div>

    `;

}

/* =====================================================
   SEND MESSAGE
   REAL BACKEND
===================================================== */

// This function will:
// 1. Get the user's question
// 2. Show the question on screen
// 3. Send the question to backend
// 4. Get the AI answer
// 5. Display the answer

async function sendMessage() {


    /* EMPTY INPUT */

    // Check if the input box is empty

    if (
        input.value.trim() === ""
    ) {

        // If input is empty, stop the function

        return;

    }


    /* GET USER QUESTION */

    // Get the text written by the user
    // trim() removes extra spaces from beginning and end

    const query =
        input.value.trim();


    /* DISABLE SEND BUTTON */

    // Disable the Send button while
    // the backend is processing the question

    sendBtn.disabled =
        true;


    /* =================================================
       CREATE USER MESSAGE
    ================================================= */

    // Create a new div for the user's message

    const message =
        document.createElement("div");


    // Add the user-message CSS class

    message.classList.add(
        "user-message"
    );


    // Put the user's question inside the div

    message.textContent =
        query;


    // Add the user message inside chatArea

    chatArea.appendChild(
        message
    );


    /* REMOVE WELCOME MESSAGE */

    // Find the Welcome message on the page

    const welcome =
        document.querySelector(
            ".welcome-message"
        );


    // If the Welcome message exists,
    // remove it from the screen

    if (welcome) {

        welcome.remove();

    }


    /* CLEAR INPUT */

    // Clear the input box after getting the question

    input.value = "";


    /* =================================================
       CREATE LOADING MESSAGE
    ================================================= */

    // Create a div for the AI loading message

    const result =
        document.createElement("div");


    // Give it the bot-message CSS class

    result.classList.add(
        "bot-message"
    );


    // Put the loading animation inside it

    result.innerHTML = `

        <div class="loading">

            <div class="loading-dots">

                <span></span>
                <span></span>
                <span></span>

            </div>

            BIS Saarthi is thinking...

        </div>

    `;


    // Add the loading message to chatArea

    chatArea.appendChild(
        result
    );


    // Scroll down to show the loading message

    scrollToBottom();


    /* =================================================
       CONNECT TO BACKEND
    ================================================= */

    // try means:
    // "Try to run this code"

    try {


        // Send the question to backend
        // askBackend() contains the common fetch code

        const data =
            await askBackend(
                query
            );


        // Show the backend response
        // in the browser console
        // useful for debugging

        console.log(  // console.log is used to print something in the browser console
            "Backend response:",
            data
        );


        /* =================================================
           GET AI ANSWER
        ================================================= */

        // Take the answer from backend
        // getAnswer() checks data.response first
        // then data.answer
        // then uses the fallback text

        const answer =
            getAnswer(
                data,
                "No response received."
            );


        // Create HTML for displaying the answer

        let html = `

            <div class="answer">

                ${
                    // Convert Markdown answer into HTML
                    marked.parse(answer)
                }

            </div>

        `;


        /* =================================================
           CONFIDENCE
        ================================================= */

        // Check if backend sent confidence

        if (
            data.confidence !== undefined
        ) {

            // Create confidence HTML
            // and add it to html

            html +=
                createConfidenceHTML(
                    data.confidence
                );

        }


        /* =================================================
           SOURCES
        ================================================= */

        // Get sources from backend

        // If backend doesn't send sources,
        // use an empty array

        const sources =
            data.sources ||
            [];


        // Check if there is at least one source

        if (
            sources.length > 0
        ) {

            // Create source HTML
            // and add it to html

            html +=
                createSourcesHTML(
                    sources
                );

        }


        /* =================================================
           ACTION BUTTONS
        ================================================= */

        // Add Copy, Like and Dislike buttons

        html +=
            createActionButtonsHTML();


        

        // Replace the loading message
        // with the actual AI answer, this will display the answer

        result.innerHTML =
            html;


        /* =================================================
           SAVE CHAT
        ================================================= */

        // Create an object containing
        // all information about this chat

        const chat = { //{} means an object was created

            // Save user's question

            question:  //here question is the property name and query is the variable
                query,


            // Save AI's answer

            answer:  //same as above question and query
                answer,


            // Save confidence value

            confidence:
                data.confidence,


            // Save sources

            sources:
                sources,


            // Save standards returned by backend

            standards:
                data.standards ||
                data.applicable_standards ||
                [],


            // Save certification information

            certification_scheme:
                data.certification_scheme ||
                data.certification,


            // Save conversation ID
            // if backend sends one

            conversation_id:
                data.conversation_id,


            // Save the current date and time

            timestamp:
                new Date().toISOString()

        };


        // Add this chat object
        // to the chatHistory array

        chatHistory.push(
            chat
        );


        // Save updated chat history
        // into browser storage

        saveHistory();


        // Update Recent Chats in sidebar

        updateRecentChats();


        /* =================================================
           UPDATE RIGHT PANEL
        ================================================= */

        // Send backend data to the function
        // that updates the right panel

        updateRightPanel(
            data
        );


        /* =================================================
           SCROLL
        ================================================= */

        // Scroll to the latest answer

        scrollToBottom();

    }


    /* =================================================
       ERROR
    ================================================= */

    // If anything inside try fails,
    // this catch block will run

    catch (error) {


        // Show the actual error
        // in the browser console

        console.error(
            "Backend error:",
            error
        );


        // Show an error message to the user

        result.innerHTML = `

            <div class="answer">

                ⚠️

                <strong>
                    Unable to connect to BIS Saarthi.
                </strong>


                <p>

                    Please check that the backend
                    server is running.

                </p>

            </div>

        `;


        // Scroll down to show the error

        scrollToBottom();

    }


    /* =================================================
       FINISH
    ================================================= */

    // finally runs whether the request
    // succeeds or fails

    finally {


        // Enable the Send button again

        sendBtn.disabled =
            false;


        // Put the Send icon back

        sendBtn.textContent =
            "➤";


        // Put the cursor back inside
        // the input box

        input.focus();

    }

}


/* =====================================================
   COPY ANSWER
===================================================== */

// This function copies the AI answer

function copyAnswer(
    button
) {


    // Find the complete bot message
    // that contains the clicked Copy button
    //.closest means find the nearest parent element and that element is bot message with the class .bot-message

    const botMessage =
        button.closest(
            ".bot-message"
        );


    // querySelector means Find the answer inside that bot message 

    const answer =
        botMessage.querySelector(
            ".answer"
        );


    // Copy the text of the answer
    // to the computer clipboard

    navigator.clipboard.writeText(
        answer.innerText
    );


    // Change the button text
    // to show that the answer was copied

    button.textContent =
        "✓ Copied";


    // Wait for 1.5 seconds
    // and change the button back to Copy

    setTimeout(
        function () {

            button.textContent =
                "📋 Copy";

        },
        1500
    );

}


/* =====================================================
   AUTO SCROLL
===================================================== */

// This function automatically scrolls
// the chat to the bottom

function scrollToBottom() {

    // Scroll the chat area

    chatArea.scrollTo({

        // Scroll all the way to the bottom

        top:
            chatArea.scrollHeight,


        // Make the scrolling smooth

        behavior:
            "smooth"

    });

}


/* =====================================================
   RIGHT PANEL
===================================================== */

// This function updates the right panel
// with standards, certification and sources

function updateRightPanel(
    data
) {


    /* =================================================
       STANDARDS
    ================================================= */

    // Get standards from backend

    // First check data.standards
    // If not available, check applicable_standards
    // If neither exists, use empty array

    const standards =
        data.standards ||
        data.applicable_standards ||
        [];


    // Check if there are no standards

    if (
        standards.length === 0
    ) {

        // Show a message saying
        // that no standards were returned

        standardsPanel.innerHTML = `

            <div class="empty-panel">

                No applicable standards
                returned for this query.

            </div>

        `;

    }


    // If standards are available

    else {

        // Clear the old standards

        standardsPanel.innerHTML =
            "";


        // Go through every standard one by one

        standards.forEach(
            function (
                standard,
                index
            ) {


                // Create a new div
                // for this standard

                const card =
                    document.createElement(
                        "div"
                    );


                // Give the div the
                // standard-card CSS class

                card.classList.add(
                    "standard-card"
                );


                // Put the standard information inside the card

                card.innerHTML = `

                    <h3>

                        ${
                            // Show standard name
                            // or standard number
                            // or default text

                            standard.name ||
                            standard.standard ||
                            "BIS Standard"
                        }

                    </h3>


                    <p>

                        ${
                            // Show standard description
                            // if available

                            standard.description ||
                            ""
                        }

                    </p>


                    ${
                        // If this is the first standard,
                        // show "Most Relevant"
                        //If index === 0 is true, show "Most Relevant".
                        //Otherwise, show nothing.

                        index === 0
                            ? `

                                <span class="relevant-badge">

                                    Most Relevant

                                </span>

                              `

                            : ""

                    }

                `;


                // Add this standard card
                // inside the standards panel

                standardsPanel.appendChild(
                    card
                );

            }
        );

    }


    /* =================================================
       CERTIFICATION
    ================================================= */

    // Get certification information
    // from the backend

    const certification =
        data.certification_scheme ||
        data.certification;


    // Check if certification information exists

    if (certification) {

        // Show the certification information

        certificationPanel.innerHTML = `

            <p class="small-text">

                Scheme Name

            </p>


            <strong>

                ${
                    // Show certification name
                    // or scheme name

                    certification.name ||
                    certification.scheme ||
                    certification

                }

            </strong>

        `;

    }


    else {

        // If there is no certification information,
        // show the empty message

        certificationPanel.innerHTML = `

            <div class="empty-panel">

                Certification information
                will appear here.

            </div>

        `;

    }


    /* =================================================
       SOURCES
    ================================================= */

    // Get sources from backend

    // If sources don't exist,
    // use an empty array

    const sources =
        data.sources ||
        [];


    // Check if there are no sources

    if (
        sources.length === 0
    ) {

        // Show a message

        sourcesPanel.innerHTML = `

            <div class="empty-panel">

                No sources returned.

            </div>

        `;

    }


    // If sources are available

    else {

        // Clear old sources

        sourcesPanel.innerHTML =
            "";


        // Add the Sources heading

        sourcesPanel.innerHTML = `

            <div class="sources-title">

                📚 Sources

            </div>

        `;


        // Go through every source one by one

        sources.forEach(
            function (source) {


                // Create a new div
                // for this source

                const item =
                    document.createElement(
                        "div"
                    );


                // Give it the panel-source CSS class

                item.classList.add(
                    "panel-source"
                );


                // Put source information inside the div

                item.innerHTML = `

                    <a
                        href="${
                            // Use source URL
                            // or source_url
                            // or "#" if unavailable

                            source.url ||
                            source.source_url ||
                            "#"
                        }"

                        target="_blank"

                        rel="noopener noreferrer" 
                    >

                        ${
                            // Show source title
                            // or source name
//noopener means New tab, don't get control over the original tab and noreferrer means Don't send the original page's URL as the referrer to the new website.
                            source.title ||
                            source.name ||
                            "BIS Document"
                        }

                    </a>


                    <p>

                        ${
                            // If clause exists,
                            // show the clause number

                            source.clause
                                ? `Clause ${source.clause} • `
                                : ""
                        }


                        ${
                            // If page exists,
                            // show the page number

                            source.page
                                ? `Page ${source.page}`
                                : ""
                        }

                    </p>

                `;


                // Add the source item
                // inside the Sources panel

                sourcesPanel.appendChild(
                    item
                );

            }
        );

    }

}


/* =====================================================
   SEND BUTTON
===================================================== */

// When the Send button is clicked,
// run the sendMessage function

sendBtn.addEventListener(
    "click",
    sendMessage
);


/* =====================================================
   ENTER KEY
===================================================== */

// Listen for keyboard actions inside the input box

input.addEventListener(
    "keydown",
    function (event) {


        // Check if the pressed key is Enter

        if (
            event.key === "Enter"
        ) {


            // Prevent the default Enter action of browser 

            event.preventDefault();


            // Send the message

            sendMessage();

        }

    }
);


/* =====================================================
   RESET CHAT
===================================================== */

// This function resets the chat screen

function resetChat() {


    // Replace the chat area
    // with the Welcome message

    chatArea.innerHTML = `

        <div class="welcome-message">

            <h1>

                👋 Welcome to BIS Saarthi

            </h1>


            <p>

                Ask me anything about BIS Standards,
                Certification, Testing Laboratories,
                or Quality Regulations.

            </p>

        </div>

    `;


    // Reset the Standards panel

    standardsPanel.innerHTML = `

        <div class="empty-panel">

            Ask a question to see
            applicable standards.

        </div>

    `;


    // Reset the Certification panel

    certificationPanel.innerHTML = `

        <div class="empty-panel">

            Certification information
            will appear here.

        </div>

    `;


    // Reset the Sources panel

    sourcesPanel.innerHTML = `

        <div class="empty-panel">

            Sources will appear
            after the AI response.

        </div>

    `;


    // Put the cursor back into the input box

    input.focus();

}


/* =====================================================
   NEW CHAT
===================================================== */

// When New Chat is clicked,
// reset the chat screen

newChatBtn.addEventListener(
    "click",
    resetChat
);


/* =====================================================
   HOME
===================================================== */

// When Home is clicked

homeBtn.addEventListener(
    "click",
    function () {

        // Use the same reset function
        // instead of writing the same code again

        resetChat();

    }
);


/* =====================================================
   FIND STANDARDS
===================================================== */

// When Find Standards is clicked

standardsBtn.addEventListener(
    "click",
    function () {


        // Create the Find Standards page
        // inside the chat area

        chatArea.innerHTML = `

            <div class="feature-page">

                <div class="feature-header">

                    <h1>

                        📋 Find BIS Standards

                    </h1>


                    <p>

                        Search for an Indian Standard
                        by product name or IS number.

                    </p>

                </div>


                <div class="feature-search">

                    <input
                        type="text"
                        id="standards-input"
                        placeholder="Example: LED bulbs or IS 16102"
                    >


                    <button
                        id="standards-search-btn"
                    >

                        Search

                    </button>

                </div>


                <div
                    id="standards-result"
                ></div>

            </div>

        `;


        // Find the newly created Standards input

        const standardsInput =
            document.getElementById(
                "standards-input"
            );


        // Find the newly created Search button

        const standardsSearchBtn =
            document.getElementById(
                "standards-search-btn"
            );


        // Find the place where search result
        // will be displayed

        const standardsResult =
            document.getElementById(
                "standards-result"
            );


        // This function searches for BIS standards

        async function searchStandards() {


            // Get the text entered by the user

            const query =
                standardsInput.value.trim();


            // If input is empty,
            // stop the function

            if (
                query === ""
            ) {

                return;

            }


            // Disable the Search button
            // while searching

            standardsSearchBtn.disabled =
                true;


            // Show loading message

            standardsResult.innerHTML = `

                <div class="feature-loading">

                    🔎 Searching BIS Standards...

                </div>

            `;


            try {


                // Send the search request to backend

                const data =
                    await askBackend(
                        `Find the relevant BIS Indian Standard for: ${query}. Give the IS number, standard title, applicability, and relevant source.`
                    );


                // Display the backend answer

                standardsResult.innerHTML = `

                    <div class="feature-result">

                        <div class="answer">

                            ${
                                marked.parse(
                                    getAnswer(
                                        data,
                                        "No standard found."
                                    )
                                )
                            }

                        </div>

                    </div>

                `;

            }


            // If something goes wrong

            catch (error) {


                // Print error in browser console

                console.error(
                    error
                );


                // Show error to user

                standardsResult.innerHTML = `

                    <div class="feature-error">

                        ⚠️ Unable to search BIS Standards.

                        <br><br>

                        Please check that the backend
                        server is running.

                    </div>

                `;

            }


            // This always runs after search finishes

            finally {


                // Enable Search button again

                standardsSearchBtn.disabled =
                    false;

            }

        }


        // When Search button is clicked,
        // run searchStandards

        standardsSearchBtn.addEventListener(
            "click",
            searchStandards
        );


        // Listen for keyboard input

        standardsInput.addEventListener(
            "keydown",
            function (event) {


                // If user presses Enter

                if (
                    event.key === "Enter"
                ) {


                    // Stop default Enter action

                    event.preventDefault();


                    // Start the search

                    searchStandards();

                }

            }
        );


        // Automatically put cursor in the input

        standardsInput.focus();

    }
);

/* =====================================================
   SETTINGS
===================================================== */

// When Settings is clicked
settingsBtn.addEventListener(
    "click",
    function () {

        // Create the Settings page
        chatArea.innerHTML = `

            <div class="feature-page">

                <div class="feature-header">

                    <h1>
                        ⚙️ Settings
                    </h1>

                    <p>
                        BIS Saarthi settings
                        and preferences.
                    </p>

                </div>


                <div class="feature-result">

                    <div class="answer">

                        <h2>
                            About BIS Saarthi
                        </h2>

                        <p>
                            BIS Saarthi is an AI assistant
                            designed to help users find
                            information about BIS Standards,
                            Certification, Testing Laboratories,
                            and Quality Regulations.
                        </p>

                    </div>

                </div>

            </div>

        `;

    }
);

/* =====================================================
   CERTIFICATION GUIDE
===================================================== */

// When Certification Guide is clicked
certificationBtn.addEventListener(
    "click",
    function () {

        chatArea.innerHTML = `

            <div class="feature-page">

                <div class="feature-header">

                    <h1>▣ Certification Guide</h1>

                    <p>
                        Learn about the BIS certification process.
                    </p>

                </div>

                <div class="guide-grid">

                    <div class="guide-card">
                        <h3>1. Identify the Standard</h3>
                        <p>
                            Find the BIS Standard applicable
                            to your product.
                        </p>
                    </div>

                    <div class="guide-card">
                        <h3>2. Product Testing</h3>
                        <p>
                            Get the product tested according
                            to the applicable BIS requirements.
                        </p>
                    </div>

                    <div class="guide-card">
                        <h3>3. Assessment</h3>
                        <p>
                            BIS assesses the product and
                            manufacturing requirements.
                        </p>
                    </div>

                    <div class="guide-card">
                        <h3>4. Licence</h3>
                        <p>
                            After completing the requirements,
                            the BIS licence can be granted.
                        </p>
                    </div>

                </div>

                <div class="feature-question">

                    <h2>Ask about BIS Certification</h2>

                    <div class="feature-search">

                        <input
                            type="text"
                            id="certification-input"
                            placeholder="Ask a certification question..."
                        >

                        <button id="certification-search-btn">
                            Search
                        </button>

                    </div>

                    <div id="certification-result"></div>

                </div>

            </div>

        `;

        const certificationInput =
            document.getElementById(
                "certification-input"
            );

        const certificationSearchBtn =
            document.getElementById(
                "certification-search-btn"
            );

        const certificationResult =
            document.getElementById(
                "certification-result"
            );


        async function askCertification() {

            const query =
                certificationInput.value.trim();

            if (!query) {
                return;
            }

            certificationResult.innerHTML = `
                <div class="feature-loading">
                    Finding certification information...
                </div>
            `;

            try {

                const data =
                    await askBackend(
                        `Answer this BIS certification question: ${query}`
                    );

                const answer =
                    getAnswer(
                        data,
                        "No certification information found."
                    );

                certificationResult.innerHTML = `
                    <div class="feature-result">
                        <div class="answer">
                            ${marked.parse(answer)}
                        </div>
                    </div>
                `;

            }
            catch (error) {

                certificationResult.innerHTML = `
                    <div class="feature-error">
                        Unable to get certification information.
                        Please try again.
                    </div>
                `;

                console.error(error);
            }
        }


        certificationSearchBtn.addEventListener(
            "click",
            askCertification
        );


        certificationInput.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Enter") {
                    askCertification();
                }

            }
        );


        certificationInput.focus();

    }
);

/* =====================================================
   LABORATORY FINDER
===================================================== */

// When Laboratory Finder is clicked
laboratoryBtn.addEventListener(
    "click",
    function () {

        chatArea.innerHTML = `

            <div class="feature-page">

                <div class="feature-header">

                    <h1>⚗ Laboratory Finder</h1>

                    <p>
                        Find BIS-recognized testing
                        laboratories.
                    </p>

                </div>

                <div class="feature-question">

                    <h2>Find a Testing Laboratory</h2>

                    <div class="feature-search">

                        <input
                            type="text"
                            id="laboratory-input"
                            placeholder="Enter your testing requirement..."
                        >

                        <button id="laboratory-search-btn">
                            Search
                        </button>

                    </div>

                    <div id="laboratory-result"></div>

                </div>

            </div>

        `;

        const laboratoryInput =
            document.getElementById(
                "laboratory-input"
            );

        const laboratorySearchBtn =
            document.getElementById(
                "laboratory-search-btn"
            );

        const laboratoryResult =
            document.getElementById(
                "laboratory-result"
            );


        async function findLaboratory() {

            const query =
                laboratoryInput.value.trim();

            if (!query) {
                return;
            }

            laboratoryResult.innerHTML = `
                <div class="feature-loading">
                    Finding suitable BIS laboratories...
                </div>
            `;

            try {

                const data =
                    await askBackend(
                        `Find BIS-recognized testing laboratories for this requirement: ${query}. Provide laboratory names, locations, relevant testing scope, and sources where available.`
                    );

                const answer =
                    getAnswer(
                        data,
                        "No laboratory information found."
                    );

                laboratoryResult.innerHTML = `
                    <div class="feature-result">
                        <div class="answer">
                            ${marked.parse(answer)}
                        </div>
                    </div>
                `;

            }
            catch (error) {

                laboratoryResult.innerHTML = `
                    <div class="feature-error">
                        Unable to find laboratories.
                        Please try again.
                    </div>
                `;

                console.error(error);
            }
        }


        laboratorySearchBtn.addEventListener(
            "click",
            findLaboratory
        );


        laboratoryInput.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Enter") {
                    findLaboratory();
                }

            }
        );


        laboratoryInput.focus();

    }
);

//for collapse
collapseBtn.addEventListener("click", function () {
    sidebar.classList.toggle("collapsed");
});