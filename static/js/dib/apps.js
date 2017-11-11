var Application = {
    loadMarktplatzInfo: function (username) {
        $.ajax({
            url: "https://marktplatz.bewegung.jetzt/u/" + username + ".json?stats=true",
            type: "GET",
            contentType: 'application/json; charset=utf-8',
            success: function(data) {
                if (typeof data.user != "undefined") {
                    var html = '<p class="card-text"><strong>Marktplatz-Info</strong></p>';

                    html += '<div class="card w-75">';
                    html += '<div class="card-block">';
                    html += '<h3 class="card-title"><a href="https://marktplatz.bewegung.jetzt/u/' + data.user.username + '">' + data.user.username + '</a></h3>';
                    html += '<h6 class="card-subtitle mb-2 text-muted">' + data.user.name + '</h6>';
                    html += '<img class="rounded-circle card-avatar" src="https://marktplatz.bewegung.jetzt' + data.user.avatar_template.replace('{size}', '80') + '" alt="Avatar">';
                    html += '</div>';
                    html += '<ul class="list-group list-group-flush">';
                    html += '<li class="list-group-item">Hauptgruppe: ' + data.user.primary_group_name + '</li>';
                    html += '<li class="list-group-item">Vertrauensstufe: ' + data.user.trust_level + '</li>';
                    html += '<li class="list-group-item">Mitglied seit: ' + Application.formatDate(data.user.created_at) + '</li>';
                    html += '<li class="list-group-item">Letzter Beitrag am: ' + Application.formatDate(data.user.last_posted_at) + '</li>';
                    html += '<li class="list-group-item">Zuletzt gesehen am: ' + Application.formatDate(data.user.last_seen_at) + '</li>';
                    html += '</ul>';
                    html += '</div>';

                    $('.card-block-user').append(html);
                }
            }
        });
    },
    formatDate: function (dateStr) {
        var date = new Date(dateStr);
        var days = date.getDate() < 10 ? '0' + date.getDate() : date.getDate();
        var minutes = date.getMinutes() < 10 ? '0' + date.getMinutes() : date.getMinutes();
        var hours = date.getHours() < 10 ? '0' + date.getHours() : date.getHours();
        var month = date.getMonth() + 1;
        month = month < 10 ? '0' + month : month;

        return days + '.' + month + '.' + date.getFullYear() + ' ' + hours + ':' + minutes + ' Uhr';
    }
};