function $i(name, p = document) {
	return p.getElementById(name);
}
function animate_base(getter, setter, from, to, dur, interp, onintr = function(proc) { return false; }, interval = 10) { // TODO this fucking closure is ruining it
	setter(from);
	let st = new Date().getTime(), oldv = getter(), timer = setInterval(function() {
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
	console.log(timer + ' (' + from + ' -> ' + to + ')');
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
