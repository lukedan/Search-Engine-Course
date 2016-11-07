"use strict";
var bookmark_width_min, bookmark_width_max;
function autoset_searchbox_height() {
	var btn1 = $i('search_proceed'), btn2 = $i('search_alt'), pmup = $i('up_pagemarker');
	var bs1 = window.getComputedStyle($i('search_input'), null);
	btn1.style.width = btn1.style.height = btn2.style.width = btn2.style.height = pmup.style.top = bs1.height;
	btn1.style.zIndex = 1;
	btn1.style.backgroundImage = 'url("/files/icons/search.ico")';
	btn1.onclick = on_search_clicked;
	btn2.style.zIndex = 0;
	btn2.style.marginLeft = 0;
	btn2.style.opacity = 0;
	btn2.style.backgroundImage = 'url("/files/icons/search_image.ico")';
	btn2.onclick = on_search_alt_clicked;

	var sdmku = $i('shadow_makeup');
	if (sdmku !== null) {
		sdmku.style.height = bs1.height;
	}
}
function autoset_mainpanel_margin() {
	var obj = $i('mainpanel'), olstyle = window.getComputedStyle($i('search_overlay'), null);
	obj.style.paddingTop =
		parseFloat(olstyle.height) +
		parseFloat(olstyle.paddingTop) +
		parseFloat(olstyle.paddingBottom);
}
function do_final_layout() {
	autoset_mainpanel_margin();
	autoset_searchbox_height();
	bookmark_width_max = parseFloat(getComputedStyle($i('up_pagemarker'), null).width);
	var downstyle = getComputedStyle($i('down_pagemarker'), null);
	bookmark_width_min = parseFloat(downstyle.width);
	$i('pagenavi_container').style.width = '0px';
	$i('pagenavi_input').style.height = downstyle.height;
}

function on_keypress(event) {
	if (event.keyCode == 13) {
		event.target.blur();
		on_search_clicked(event);
	}
}

var color_table = new Map();
var hsl_gen = hsl_generator();
function append_text_response(respjson) {
	if (respjson.lst.length == 0) {
		return;
	}
	var mainpnl = $i('mainpanel');
	var subpnl = document.createElement('div');
	$i('up_pagemarker').style.visibility = 'visible';
	subpnl.innerHTML = `
		<div class="blurred_pagemarker">
			<p class="pagemarker" onclick="on_pagemarker_clicked(event);">${current_page + 1}</p>
		</div>
	`;
	for (var i = 0; i < respjson.lst.length; ++i) {
		var curentry = respjson.lst[i];

		var node = document.createElement('a');
		node.className = 'searched_item';
		node.href = curentry.url;
		node.target = '_blank';

		var summarystr = '';
		if (curentry.ellbef) {
			summarystr = '...';
		}
		var curmak = false;
		for (var j = 0; j < curentry.lst.length; ++j, curmak = !curmak) {
			if (!curmak) {
				summarystr += curentry.lst[j];
			} else {
				if (color_table[curentry.lst[j]] === undefined) {
					color_table[curentry.lst[j]] = rgb_to_str(hsl_to_rgb(hsl_gen.next().value));
				}
				summarystr += `<em style="background: rgba(${color_table[curentry.lst[j]]}, 0.6);">${curentry.lst[j]}</em>`;
			}
		}
		if (curentry.ellaft) {
			summarystr += '...';
		}

		node.innerHTML = `
			<div class="blurred_floater_bkgtrans">
				<h3>${curentry.titletext}</h3>
				<p>${summarystr}</p>
				<div>
					<small>${curentry.urltext}</small>
				</div>
				<div class="searched_item_background"></div>
			</div>
		`;

		subpnl.appendChild(node);
	}
	mainpnl.appendChild(subpnl);
	animate_style_property(subpnl, 'opacity', 0.0, 1.0, '', 200);
	check_pagemarkers();
}

var img_curid, img_update_timer = null, img_toth, img_fstofrow_id, img_row_w, img_default_height = 200;
function layout_single_image(father, totw, pos, doanimate = true) {
	var obj = father.children[pos], cw = img_default_height * obj.naturalWidth / obj.naturalHeight;
	obj.style.width = cw;
	obj.style.height = img_default_height;
	obj.style.marginTop = img_toth;
	obj.style.marginLeft = img_row_w;
	while (img_row_w + cw > totw) {
		var end_id = pos, ratio = img_row_w / totw;
		if (pos == img_fstofrow_id || 1.0 - ratio < (img_row_w + cw) / totw - 1.0) {
			ratio = (img_row_w + cw) / totw;
			img_toth += img_default_height / ratio;
			++end_id;
			img_row_w = -cw;
		} else {
			img_toth += img_default_height / ratio;
			obj.style.marginTop = img_toth;
			obj.style.marginLeft = 0;
			img_row_w = 0.0;
		}
		var left = 0;
		for (var curimg = img_fstofrow_id; curimg < end_id; ++curimg) {
			var tmp = father.children[curimg], bcr = tmp.getBoundingClientRect(), mw = bcr.width / ratio;
			if (!doanimate || pos == curimg || tmp.style.opacity < 0.2) {
				tmp.style.width = mw;
				tmp.style.height = bcr.height / ratio;
				tmp.style.marginLeft = left;
			} else {
				animate_style_property_to(tmp, 'width', mw, 'px', 200, eased_interp);
				animate_style_property_to(tmp, 'height', bcr.height / ratio, 'px', 200, eased_interp);
				animate_style_property_to(tmp, 'marginLeft', left, 'px', 200, eased_interp);
			}
			left += mw;
		}
		img_fstofrow_id = end_id;
	}
	img_row_w += cw;
}
function relayout_images() {
	var father = $i('mainpanel').children[0], totw = father.getBoundingClientRect().width;
	img_fstofrow_id = img_toth = img_row_w = 0;
	for (var i = 0; i < img_curid; ++i) {
		layout_single_image(father, totw, i, false);
	}
}
window.onresize = function() {
	relayout_images();
	check_load_nextpage();
};
function on_img_update() {
	var father = $i('mainpanel').children[0], totw = father.getBoundingClientRect().width;
	while (img_curid < father.children.length && father.children[img_curid].complete) {
		var obj = father.children[img_curid];
		if (obj.naturalHeight < 50 || obj.naturalWidth < 50) {
			obj.parentNode.removeChild(obj);
		} else {
			layout_single_image(father, totw, img_curid);
			obj.style.visibility = 'visible';
			animate_style_property(obj, 'opacity', 0.0, 1.0, 0.0, 500);
			++img_curid;
		}
	}
	if (img_curid >= father.children.length) {
		$i('down_pagemarker').style.visibility = 'hidden';
		check_load_nextpage();
		clearInterval(img_update_timer);
		img_update_timer = null;
	}
}
function start_img_update() {
	if (img_update_timer === null) {
		img_update_timer = setInterval(on_img_update, 500);
	}
}
function append_image_response(respjson) {
	if (respjson.lst.length == 0) {
		return;
	}
	var mainpnl = $i('mainpanel').children[0];
	for (var i = 0; i < respjson.lst.length; ++i) {
		var curentry = respjson.lst[i], cobj = document.createElement('img');
		cobj.src = '/getimg?url=' + encodeURI(curentry.url) + '&ref=' + encodeURI(curentry.pageurl);
		cobj.style.width = 0.0;
		cobj.style.height = 0.0;
		cobj.style.visibility = 'hidden';
		cobj.style.position = 'absolute';
		cobj.className = 'image_resultitem';
		cobj.style.zIndex = 0;
		cobj.alt = curentry.pageurl;
		cobj.addEventListener('mouseenter', function(event) {
			event.target.style.zIndex = parseFloat(event.target.style.zIndex) + 2;
		});
		cobj.addEventListener('mouseleave', function(event) {
			event.target.style.zIndex = parseFloat(event.target.style.zIndex) - 1;
			var timer = setInterval(function() {
				event.target.style.zIndex = parseFloat(event.target.style.zIndex) - 1;
				clearInterval(timer);
			}, 300);
		});
		cobj.addEventListener('click', function(event) {
			window.open(event.target.alt);
		});
		mainpnl.appendChild(cobj);
	}
	start_img_update();
}

var current_page = -1, start_page = 0;
var search_content = '';
var waiting = false;
function start_loading() {
	if (waiting) {
		return false;
	}
	var dpm = $i('down_pagemarker');
	dpm.children[0].style.backgroundImage = 'url("/files/icons/loading.gif")';
	dpm.children[0].style.color = 'transparent';
	dpm.style.visibility = 'visible';
	waiting = true;
	window.status = 'Loading...';
	return true;
}
var on_response = append_text_response;
function do_request_search_nosetwait() {
	var request = new XMLHttpRequest();
	request.onreadystatechange = function() {
		if (request.readyState == 4) {
			waiting = false;
			if (request.status == 200) {
				on_response(JSON.parse(request.responseText));
			} else {
				--current_page;
			}
			window.status = '';
		}
	};
	var tgstr = (on_response === append_text_response ? 'search' : 'searchimg');
	request.open('GET', tgstr + '?target=' + search_content + '&page=' + current_page, true);
	request.send();
}
function do_request_search() {
	if (start_loading()) {
		do_request_search_nosetwait();
	}
}
function on_initialize_new_search(event) {
	if (start_loading()) {
		color_table = new Map();
		hsl_gen = hsl_generator();
		$i('up_pagemarker').style.visibility = 'hidden';
		var inputbox = $i('search_input'), mainpnl = $i('mainpanel');
		mainpnl.innerHTML = '';
		search_content = inputbox.value;
		start_page = current_page = 0;
		if (on_response === append_image_response) {
			if (img_update_timer !== null) {
				clearInterval(img_update_timer);
				img_update_timer = null;
			}
			if (mainpnl.children.length == 0) {
				mainpnl.innerHTML = '<div class="image_search_left_pnl"></div>';
			}
			img_curid = img_fstofrow_id = img_row_w = img_toth = 0;
			document.title = search_content + ' - Image Search';
		} else {
			if (img_update_timer !== null) {
				clearInterval(img_update_timer);
				img_update_timer = null;
			}
			document.title = search_content + ' - Search';
		}
		do_request_search_nosetwait();
	}
}
function on_jump(event) {
	if (event.keyCode != 13) {
		return;
	}
	if (start_loading()) {
		$i('up_pagemarker').style.visibility = 'hidden';
		var mainpnl = $i('mainpanel');
		mainpnl.innerHTML = '';
		start_page = current_page = parseInt($i('pagenavi_input').value) - 1;
		do_request_search_nosetwait();
		event.target.value = '';
		event.target.blur();
	}
}
function get_next_page() {
	if (current_page >= 0) {
		if (start_loading()) {
			++current_page;
			do_request_search_nosetwait();
		}
	}
}
function check_load_nextpage() {
	var top = document.body.scrollHeight - document.body.clientHeight;
	if (document.body.scrollTop > top - 100) {
		get_next_page();
	}
	check_pagemarkers();
}

function check_pagemarkers() {
	if (on_response !== append_text_response) {
		return;
	}
	var
		children = $i('mainpanel').children,
		uppm = $i('up_pagemarker'),
		upr = uppm.getBoundingClientRect(),
		dpm = $i('down_pagemarker'),
		dpr = dpm.getBoundingClientRect(),
		bset = false;
	for (var i = 0; i < children.length; ++i) {
		var marker = children[i].children[0], rect = marker.getBoundingClientRect();
		if (rect.top < upr.top) {
			marker.style.visibility = 'hidden';
			uppm.children[0].innerHTML = marker.children[0].innerHTML;
		} else if (rect.bottom > dpr.bottom) {
			marker.style.visibility = 'hidden';
			if (!bset) {
				bset = true;
				dpm.children[0].innerHTML = marker.children[0].innerHTML;
			}
		} else {
			marker.style.width = Math.min((dpr.top - rect.top) * 0.3 + bookmark_width_min, bookmark_width_max);
			marker.style.visibility = 'visible';
		}
	}
	if (!bset) {
		dpm.children[0].innerHTML = '_';
		dpm.children[0].style.color = 'transparent';
		if (!waiting) {
			dpm.children[0].style.backgroundImage = 'url("/files/icons/bottom.ico")';
		}
	} else {
		dpm.children[0].style.backgroundImage = '';
		dpm.children[0].style.color = '#000000';
	}
}
function on_pagemarker_clicked(event) {
	if (on_response !== append_text_response) {
		return;
	}
	if (event.target.innerHTML === '_') {
		var tar = document.body.scrollHeight - document.body.clientHeight;
	} else {
		var
			tgm = $i('mainpanel').children[parseInt(event.target.innerHTML) - start_page - 1],
			border = tgm.getBoundingClientRect(),
			tar = document.body.scrollTop + border.top - 0.2 * document.body.clientHeight;
		if (tar < 0) {
			tar = 0;
		}
	}
	animate_property_to(document.body, 'scrollTop', tar, 500, eased_interp);
}

function on_search_clicked(event) {
	on_initialize_new_search(event);
}
function on_search_alt_clicked(event) {
	if (on_response === append_text_response) {
		on_response = append_image_response;
	} else {
		on_response = append_text_response;
	}
	var prm = $i('search_proceed'), scd = $i('search_alt'), t;

	t = prm.id;
	prm.id = scd.id;
	scd.id = t;

	prm.onclick = on_search_alt_clicked;
	scd.onclick = on_search_clicked;

	prm.style.zIndex = 0;
	scd.style.zIndex = 1;

	animate_style_property_to(prm, 'marginLeft', 0, 'px', 200, eased_interp);
	animate_style_property_to(scd, 'marginLeft', 0, 'px', 200, eased_interp);

	animate_style_property_to(prm, 'opacity', 0, 0, 200, eased_interp);
	animate_style_property_to(scd, 'opacity', 1, 0, 200, eased_interp);

	on_initialize_new_search(event);
}
function on_buttons_mouseenter(event) {
	var obj = $i('search_alt');
	animate_style_property_to(obj, 'marginLeft', parseFloat(obj.style.width), 'px', 200, eased_interp);
	animate_style_property_to(obj, 'opacity', 1, 0, 200, eased_interp);
}
function on_buttons_mouseleave(event) {
	var obj = $i('search_alt');
	animate_style_property_to(obj, 'marginLeft', 0, 'px', 200, eased_interp);
	animate_style_property_to(obj, 'opacity', 0, 0, 200, eased_interp);
}

var pagemarker_mouseover = 0, jumptextbox_focus = false;
function on_pagemarker_addref(event) {
	if (on_response !== append_text_response) {
		return;
	}
	++pagemarker_mouseover;
	var obj = $i('pagenavi_container');
	animate_style_property_to(obj, 'width', 150, 'px', 200, eased_interp);
}
function on_pagemarker_decref(event) {
	if (on_response !== append_text_response) {
		return;
	}
	--pagemarker_mouseover;
	var obj = $i('pagenavi_container');
	var timer = setInterval(function() {
		if (!(pagemarker_mouseover > 0 || jumptextbox_focus)) {
			animate_style_property_to(obj, 'width', 0, 'px', 200, eased_interp);
		}
		clearInterval(timer);
	}, 500);
}
