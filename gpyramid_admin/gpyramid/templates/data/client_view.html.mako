<!DOCTYPE html>
<html>
<head>
<title>Oauth2 Client: ${client.client_id}</title>
<style type="text/css">
	td, th { padding: 0.25em 1em }
</style>
</head>
<body>
<p>
<a href="..">Back to list of clients</a>
</p>

<h1>Add Edit</h1>
<p/>
<p>
<form method="POST" ><table>
	<tr><th>Client ID</th><td>${client.client_id}</td></tr>
% for field in (form.client_secret, form.name, form.client_type, form.email, form.redirect_uri, form.home_page):
	<tr><th>${ field.label }</th><td>${ field() }<td></tr>
	% if field.errors:
	<tr><th></th><td>
		<ul>
		% for error in field.errors:
			<li>${ error }</li>
		% endfor
		</ul>
	</td></tr>
	% endif
% endfor
	<tr><th></th><td><input type="submit" value="Edit Client" /></td></tr>
</table></form>
</p>
<p>
<ul>
	<li><button id="delete_button">Delete Client</button></li>
</ul>
</p>
<script type="text/javascript">
(function(window) {
	function on_delete_click() {
		// Confirm Delete of user before performing action.
		var response = window.confirm("Are you sure you want to delete client?");
		if (response === true) {
			// Delete confirmed.
			// http://www.w3schools.com/xml/dom_http.asp
			var xmlhttp = new XMLHttpRequest();
			xmlhttp.onreadystatechange = function() {
				if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
					// Delete took place, look at list of clients now.
					var pathname = document.location.pathname;
					if (pathname.endsWith("/")) {
						pathname = pathname.slice(0, pathname.length - 1);
					}
					document.location.href = pathname.slice(0, pathname.lastIndexOf("/") + 1);
				}
			};
			xmlhttp.open("DELETE", window.location, true);
			xmlhttp.send();
		}
		return false;
	}
	document.getElementById("delete_button").addEventListener("click", on_delete_click);

})(window);

</script>
</body>
</html>
<!--
# vim: set syntax=mako ts=2 sts=2 ai
-->
