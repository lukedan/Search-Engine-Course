function $i(name, p = document) {
	return p.getElementById(name);
}
function animate_base(getter, setter, from, to, dur, interp, onintr = function(proc) { return false; }, interval = 10) { // had to do it myself
	setter(from);
	var st = new Date().getTime(), oldv = getter(), timer = setInterval(function() {
		var rng = (new Date().getTime() - st) / dur;
		if (getter() != oldv) {
			if (!onintr(rng)) {
				clearInterval(timer);
				return;
			}
		}
		if (rng > 1.0) {
			setter(to);
			clearInterval(timer);
			return;
		}
		setter(from + (to - from) * interp(rng));
		oldv = getter();
	}, interval);
}
function linear_interp(v) {
	return v;
}
function eased_interp(v) {
	if (v < 0.5) {
		return 2.0 * v * v;
	} else {
		v = 1.0 - v;
		return 1.0 - 2.0 * v * v;
	}
}
function animate_property_to(obj, prop, to, dur, interp = linear_interp, onintr = function(proc) { return false; }, interval = 10) {
	animate_base(function() {
		return obj[prop];
	}, function(val) {
		obj[prop] = val;
	}, obj[prop], to, dur, interp, onintr, interval);
}
function animate_style_property(obj, prop, from, to, unit, dur, interp = linear_interp, onintr = function(proc) { return false; }, interval = 10) {
	animate_base(function() {
		return obj.style[prop];
	}, function(val) {
		obj.style[prop] = val + unit;
	}, from, to, dur, interp, onintr, interval);
}
function animate_style_property_to(obj, prop, to, unit, dur, interp = linear_interp, onintr = function(proc) { return false; }, interval = 10) {
	animate_base(function() {
		return obj.style[prop];
	}, function(val) {
		obj.style[prop] = val + unit;
	}, parseFloat(obj.style[prop]), to, dur, interp, onintr, interval);
}

var bookmark_width_min, bookmark_width_max;
function autoset_searchbox_height() {
	var btn = $i('search_proceed'), pmup = $i('up_pagemarker');
	var bs1 = window.getComputedStyle($i('search_input'), null);
	btn.style.width = btn.style.height = pmup.style.top = bs1.height;

	var sdmku = $i('shadow_makeup');
	if (sdmku !== null) {
		sdmku.style.height = bs1.height;
	}
}
function autoset_mainpanel_margin() {
	var obj = $i('mainpanel');
	var olstyle = window.getComputedStyle($i('search_overlay'), null);
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
		on_initialize_new_search(event);
	}
}

function hsl_to_rgb(hsl) {
	var c = (1.0 - Math.abs(2.0 * hsl.l - 1.0)) * hsl.s;
	var x = c * (1.0 - Math.abs((hsl.h % 2) - 1.0));
	if (hsl.h < 1.0) {
		var rgb = {'r': c, 'g': x, 'b': 0.0};
	} else if (hsl.h < 2.0) {
		var rgb = {'r': x, 'g': c, 'b': 0.0};
	} else if (hsl.h < 3.0) {
		var rgb = {'r': 0.0, 'g': c, 'b': x};
	} else if (hsl.h < 4.0) {
		var rgb = {'r': 0.0, 'g': x, 'b': c};
	} else if (hsl.h < 5.0) {
		var rgb = {'r': x, 'g': 0.0, 'b': c};
	} else if (hsl.h < 6.0) {
		var rgb = {'r': c, 'g': 0.0, 'b': x};
	} else {
		var rgb = {'r': 0.0, 'g': 0.0, 'b': 0.0};
	}
	var m = hsl.l - 0.5 * c;
	return {'r': rgb.r + m, 'g': rgb.g + m, 'b': rgb.b + m};
}
function rgb_to_str(rgb) {
	var result =
		String(Math.floor(255.0 * rgb.r)) + ', ' +
		String(Math.floor(255.0 * rgb.g)) + ', ' +
		String(Math.floor(255.0 * rgb.b));
	return result;
}
function* hsl_generator(s = 1.0, l = 0.7) {
	var divpm = 1.0;
	while (true) {
		var curv = 1.0 + 0.5 * divpm;
		while (curv < 7.0) {
			yield {'h': curv % 6.0, 's': s, 'l': l};
			curv += divpm;
		}
		divpm *= 0.5;
	}
}

var color_table = new Map();
var hsl_gen = hsl_generator();
function add_response_to_list(respjson) {
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
	waiting = true;
	window.status = 'Loading...';
	return true;
}
function do_request_search_nosetwait() {
	var request = new XMLHttpRequest();
	request.onreadystatechange = function() {
		if (request.readyState == 4) {
			waiting = false;
			if (request.status == 200) {
				add_response_to_list(JSON.parse(request.responseText));
			} else {
				--current_page;
			}
			window.status = '';
		}
	};
	request.open('GET', 'search?target=' + search_content + '&page=' + current_page, true);
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
		$i('down_pagemarker').style.visibility = 'visible';
		var inputbox = $i('search_input'), mainpnl = $i('mainpanel');
		mainpnl.innerHTML = '';
		search_content = inputbox.value;
		document.title = search_content + ' - Search';
		start_page = current_page = 0;
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

var pagemarker_mouseover = 0, jumptextbox_focus = false;
function on_pagemarker_addref(event) {
	++pagemarker_mouseover;
	var obj = $i('pagenavi_container');
	animate_style_property_to(obj, 'width', 150, 'px', 100, eased_interp);
}
function on_pagemarker_decref(event) {
	--pagemarker_mouseover;
	var obj = $i('pagenavi_container');
	var timer = setInterval(function() {
		if (!(pagemarker_mouseover > 0 || jumptextbox_focus)) {
			animate_style_property_to(obj, 'width', 0, 'px', 100, eased_interp);
		}
		clearInterval(timer);
	}, 500);
}
