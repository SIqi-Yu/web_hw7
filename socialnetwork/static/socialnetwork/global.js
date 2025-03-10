/* ----------------- CSRF Setup (AJAX) --------------------- */
function getCookie(name) {
    if (!document.cookie) return null;
    const xsrfCookies = document.cookie.split(';').map(c => c.trim()).filter(c => c.startsWith(name + '='));
    if (xsrfCookies.length === 0) return null;
    return decodeURIComponent(xsrfCookies[0].split('=')[1]);
}
const csrftoken = getCookie('csrftoken');

function setupAjax() {
  // For older versions of jQuery you’d do:
  //   $.ajaxSetup({...});
  // If you’re using fetch, do something like:
  // ...
}

setupAjax();

/* ----------------- Utility: Format date/time -------------- */
function formatDate(isoString) {
    // Create JS Date from ISO format
    let d = new Date(isoString);
    // You can manipulate how the date/time is displayed. Example:
    // toLocaleDateString and toLocaleTimeString
    // e.g., "M/D/YYYY h:mm AM/PM"
    let optionsDate = { year: 'numeric', month: 'numeric', day: 'numeric' };
    let optionsTime = { hour: 'numeric', minute: '2-digit' };
    return d.toLocaleDateString('en-US', optionsDate) + ' ' + d.toLocaleTimeString('en-US', optionsTime);
}

/* ----------------- Duplicate Detection --------------------- */
function postExists(postId) {
    return document.getElementById("id_post_div_" + postId) !== null;
}

function commentExists(commentId) {
    return document.getElementById("id_comment_div_" + commentId) !== null;
}

/* ----------------- DOM Updaters --------------------------- */

// Add a single post to the page (if it doesn’t already exist)
function addPostToDOM(post) {
    if (postExists(post.id)) {
        return;  // If we already have it, do nothing
    }
    let container = document.getElementById("posts-container");

    // Create the outer div
    let postDiv = document.createElement("div");
    postDiv.className = "post-div";
    postDiv.id = "id_post_div_" + post.id;

    // Create the post HTML (example approach, you can build with createElement)
    let postHTML = `
      <p>
        <a id="id_post_profile_${post.id}" href="/profile/${post.user_id}">
          ${post.first_name} ${post.last_name}
        </a> –
        <span id="id_post_text_${post.id}">
          ${post.text}
        </span>
      </p>
      <p id="id_post_date_time_${post.id}">
        ${formatDate(post.creation_time)}
      </p>

      <div class="comment-container" id="id_comment_container_${post.id}">
      </div>

      <label>Comment:</label>
      <input type="text" id="id_comment_input_text_${post.id}" />
      <button type="button" onclick="addComment(${post.id})" id="id_comment_button_${post.id}">Submit</button>
    `;
    postDiv.innerHTML = postHTML;
    container.insertBefore(postDiv, container.firstChild); // Insert at top if you want newest first
}

// Add a single comment to the page
function addCommentToDOM(postId, comment) {
    if (commentExists(comment.id)) return;
    let commentContainer = document.getElementById("id_comment_container_" + postId);

    let cDiv = document.createElement("div");
    cDiv.className = "comment-div";
    cDiv.id = "id_comment_div_" + comment.id;

    cDiv.innerHTML = `
      <a id="id_comment_profile_${comment.id}"
         href="/profile/${comment.user_id}">
         ${comment.first_name} ${comment.last_name}
      </a>
      <span id="id_comment_text_${comment.id}">
        ${comment.text}
      </span>
      <p id="id_comment_date_time_${comment.id}">
        ${formatDate(comment.creation_time)}
      </p>
    `;
    commentContainer.appendChild(cDiv);
}

/* ----------------- Refresh Streams via AJAX --------------- */

function refreshGlobalStream() {
    // We'll use the fetch API as an example
    fetch("/socialnetwork/get-global", {
        method: "GET",
        headers: {
            "X-CSRFToken": csrftoken,
        }
    })
    .then(response => {
        if (!response.ok) throw new Error("Network response was not ok (GET)");
        return response.json();
    })
    .then(data => {
        let posts = data.posts;
        // For each post, either add it or skip if it’s already in the DOM
        posts.forEach(post => {
            addPostToDOM(post);
            // For each comment in that post, add it
            post.comments.forEach(comment => {
                addCommentToDOM(post.id, comment);
            });
        });
    })
    .catch(err => {
        console.log("Error in refreshGlobalStream:", err);
    });
}

/* ----------------- Add Comment via AJAX -------------------- */
function addComment(postId) {
    let input = document.getElementById("id_comment_input_text_" + postId);
    let textValue = input.value.trim();
    if (!textValue) return;

    // Clear the input field
    input.value = "";

    let formData = new FormData();
    formData.append("comment_text", textValue);
    formData.append("post_id", postId);

    fetch("/socialnetwork/add-comment", {
        method: "POST",
        body: formData,
        headers: {
            "X-CSRFToken": csrftoken,
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Network response was not ok for addComment");
        }
        return response.json();
    })
    .then(data => {
        // The response includes the "comment" object
        if (data.comment) {
            addCommentToDOM(postId, data.comment);
        }
    })
    .catch(err => {
        console.log("Error in addComment:", err);
    });
}

/* ----------------- Periodic Refresh (every 5 seconds) ------ */

// Initial load
refreshGlobalStream();

// Poll every 5 seconds
setInterval(refreshGlobalStream, 5000);