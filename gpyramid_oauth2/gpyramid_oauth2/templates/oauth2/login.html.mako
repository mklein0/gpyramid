<!DOCTYPE html>
<html>
<head>
<title>Login Page</title>
</head>
<body>

<p>
<form method="POST"><table>
% for field in (form.username, form.password):
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
	% if form.hidden.errors:
	<tr><th></th><td>
		<ul>
		% for error in form.hidden.errors:
			<li>${ error }</li>
		% endfor
		</ul>
	</td></tr>
	% endif
	<tr><th></th><td><input type="submit" value="Login" /></td></tr>
</table></form>
</p>
</body>
</html>
