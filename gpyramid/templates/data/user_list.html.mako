<!DOCTYPE html>
<html>
<head>
<title>List of Users</title>
<style type="text/css">
	td, th { padding: 0.25em 1em }
</style>
</head>
<body>
<h1>List of Users</h1>

% if paginator.items:
${paginator.pager() | n}
<p>
<table border="1">
	<tr>
		<th></th>
		<th>Username</th>
		<th>UUID</th>
		<th>Email</th>
		<th>Last Login At</th>
	</tr>
% for pos, user in enumerate(paginator.items, (items_per_page * (page_num - 1) + 1)):
	<tr>
		<td>${pos}.</td>
		<td><a href="${request.route_path('data.user.view_or_edit', user_uuid=user.user_uuid)}">${user.username}</a></td>
		<td>${user.user_uuid}</td>
		<td>${user.email}</td>
		<td>${user.last_login_at}</td>
	</tr>

% endfor
</table>
</p>
${paginator.pager() | n}

%else:
<ul>
	<li><strong>No Users Found.</strong></li>
</ul>

%endif
<h1>Add User</h1>
<p/>
<form method="POST" ><table>
% for field in (form.username, form.email, form.user_uuid):
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
	<tr><th></th><td><input type="submit" value="Add New User" /></td></tr>
</table></form>
</body>
</html>
<!--
# vim: set syntax=mako ts=2 sts=2 ai
-->
