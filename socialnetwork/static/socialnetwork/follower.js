
function getCookie(name) {
    if (!document.cookie) return null;
    const xsrfCookies = document.cookie
        .split(';')
        .map(c => c.trim())
        .filter(c => c.startsWith(name + '='));
    if (xsrfCookies.length === 0) return null;
    return decodeURIComponent(xsrfCookies[0].split('=')[1]);
}
const csrftoken = getCookie('csrftoken');

function formatDate(isoString) {
    let d = new Date(isoString);
    let optionsDate = { year: 'numeric', month: 'numeric', day: 'numeric' };
    let optionsTime = { hour: 'numeric', minute: '2-digit' };
    return d.toLocaleDateString('en-US', optionsDate) + ' ' + d.toLocaleTimeString('en-US', optionsTime);
}

function postExists(postId) {
    return document.getElementById("id_post_div_" + postId) !== null;
}

function commentExists(commentId) {
    return document.getElementById("id_comment_div_" + commentId) !== null;
}

function addPostToDOM(post) {
    if (postExists(post.id)) return;
    let container = document.getElementById("posts-container");
    let postDiv = document.createElement("div");
    postDiv.className = "post-div";
    postDiv.id = "id_post_div_" + post.id;
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
      <div class="comment-container" id="id_comment_container_${post.id}"></div>
      <label>Comment:</label>
      <input type="text" id="id_comment_input_text_${post.id}" />
      <button type="button" onclick="addComment(${post.id})" id="id_comment_button_${post.id}">Submit</button>
    `;
    postDiv.innerHTML = postHTML;
    container.insertBefore(postDiv, container.firstChild);
}

function addCommentToDOM(postId, comment) {
    if (commentExists(comment.id)) return;
    let commentContainer = document.getElementById("id_comment_container_" + postId);
    let cDiv = document.createElement("div");
    cDiv.className = "comment-div";
    cDiv.id = "id_comment_div_" + comment.id;

    cDiv.innerHTML = `
      <a id="id_comment_profile_${comment.id}" href="/profile/${comment.user_id}">
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

function refreshFollowerStream() {
    fetch("/socialnetwork/get-follower", {
        method: "GET",
        headers: {
            "X-CSRFToken": csrftoken,
        }
    })
    .then(response => {
        if (!response.ok) throw new Error("Network response was not ok for get-follower");
        return response.json();
    })
    .then(data => {
        let posts = data.posts;
        posts.forEach(post => {
            addPostToDOM(post);
            post.comments.forEach(comment => {
                addCommentToDOM(post.id, comment);
            });
        });
    })
    .catch(err => {
        console.log("Error in refreshFollowerStream:", err);
    });
}

function addComment(postId) {
    let input = document.getElementById("id_comment_input_text_" + postId);
    let textValue = input.value.trim();
    if (!textValue) return;
    input.value = "";
    let formData = new FormData();
    formData.append("comment_text", textValue);
    formData.append("post_id", postId);

    fetch("/socialnetwork/add-comment", {
        method: "POST",
        body: formData,
        headers: {
            "X-CSRFToken": csrftoken,
        }
    })
    .then(response => {
        if (!response.ok) throw new Error("Network response was not ok for addComment");
        return response.json();
    })
    .then(data => {
        if (data.comment) {
            addCommentToDOM(postId, data.comment);
        }
    })
    .catch(err => {
        console.log("Error in addComment:", err);
    });
}

refreshFollowerStream();
setInterval(refreshFollowerStream, 5000);
