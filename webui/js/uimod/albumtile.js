
"use strict";

/*
 *
 * Requirements:
 *   - JQuery
 *   - albumtile.css
 * Show:
 * Functions:
 * Callbacks:
 * Recommended Paths:
 * Trigger: (fnc -> sig)
 *   - GetAlbum -> ShowAlbum
 *
 */

function CreateAlbumTile(MDBAlbum)
{
    return _CreateAlbumTile(MDBAlbum, "medium");
}
function CreateSmallAlbumTile(MDBAlbum)
{
    return _CreateAlbumTile(MDBAlbum, "small");
}

// valid sizes: medium, small
function _CreateAlbumTile(MDBAlbum, size)
{
    var html        = "";
    var imgpath     = EncodeArtworkPath(MDBAlbum.artworkpath, "150x150");
    var albumid     = MDBAlbum.id;
    var albumname   = OptimizeAlbumName(MDBAlbum.name);
    var albumrelease= MDBAlbum.release;
    var albumrequest= "MusicDB_Request(\'GetAlbum\', \'ShowAlbum\', {albumid:"+albumid+"});";
    var datawidth   = "data-size=\"" + size + "\"";

    html += "<div";
    html += " class=\"AT_albumentry\"";
    html += " " + datawidth;
    html += " onClick=\"" + albumrequest + "\"";
    html += ">";

    // Cover
    html += "<div title=\"Show this Album\" class=\"AT_albumcover\" " + datawidth + ">";
    html += "<img src=\"" + imgpath + "\">";
    html += "</div>";
    
    html += "<div class=\"AT_albummetadata\">";
    if(size != "small")
        html += "<span class=\"AT_albumrelease hlcolor smallfont\">" + albumrelease + "</span>";
    html += "<span class=\"AT_albumname fgcolor smallfont\" title=\""+albumname+"\">" + albumname + "</span>";
    html += "</div>";

    html += "</div>";

    return html;
}


function OptimizeAlbumName(albumname)
{
    var name = albumname;

    // Remove "notes"
    var startofnote = name.indexOf("(", 1); // do not recognive an albumname starting with ( as note
    if(startofnote > 0)
    {
        name = name.substring(0, startofnote);
    }

    // Remove suffixed
    name = _RemoveSuffix(name, " - EP");
    name = _RemoveSuffix(name, " - Single");

    // Remove edition-Info: " - * Edition"
    var startofedition = name.search(/\s-\s\D*\sEdition/);
    if(startofedition > 0)
    {
        name = name.substring(0, startofedition);
    }

    // Make nicer dashes
    name = name.replace(" - ", " – ");
    return name;
}


function _RemoveSuffix(albumname, suffix)
{
    var startofsuffix = albumname.indexOf(suffix);
    if(startofsuffix > 0)
    {
        albumname = albumname.substring(0, startofsuffix);
    }
    return albumname;
}

// vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

