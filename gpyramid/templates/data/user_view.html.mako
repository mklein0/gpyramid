<!DOCTYPE html>
<html>
<head>
<title>User: ${user.username}</title>
<style type="text/css">
	td, th { padding: 0.25em 1em }
</style>
</head>
<body>
<p>
<a href="..">Back to user list</a>
</p>
<h1>Edit User</h1>

<p/>
<p>
<form method="POST" ><table>
	<tr><th>UUID</th><td>${user.user_uuid}</td></tr>
% for field in (form.username, form.email,):
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
	<tr><th>Last Login At</th><td>${user.last_login_at}</td></tr>
	<tr><th></th><td><input type="submit" value="Edit User" /></td></tr>
</table></form>
</p>
<p>
<ul>
	<li><button id="delete_button">Delete User</button</li>
</ul>
</form>
</p>
<script type="text/javascript">
(function(window) {
	function on_delete_click() {
		// Confirm Delete of user before performing action.
		var response = window.confirm("Are you sure you want to delete user?");
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
