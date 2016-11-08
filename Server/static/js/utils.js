function $i(name, p = document) {
	return p.getElementById(name);
}

var _active_anis = [], _ani_tmr = null;
function _ani_obj(getter, setter, from, to, dur, interp, unq, unqcheck, onintr) {
	this.getter = getter;
	this.setter = setter;
	this.from = from;
	this.to = to;
	this.dur = dur;
	this.interp = interp;
	this.onintr = onintr;

	this.fromt = new Date().getTime();
	this.setter(from);
	this.unqcheck = unqcheck;
	unq(this);
}
_ani_obj.prototype.update = function(curt) {
	var rng = (curt - this.fromt) / this.dur;
	if (!this.unqcheck(this)) {
		if (!this.onintr(rng)) {
			return false;
		}
	}
	if (rng > 1.0) {
		this.setter(this.to);
		return false;
	}
	this.setter(this.from + (this.to - this.from) * this.interp(rng));
	return true;
};
function _update_animation() {
	_active_anis.sort(function(a, b) {
		return a.fromt - b.fromt;
	});
	var curt = new Date().getTime();
	for (var i = _active_anis.length; i > 0; ) {
		var curani = _active_anis[--i];
		if (!curani.update(curt)) {
			_active_anis[i] = _active_anis[_active_anis.length - 1];
			_active_anis.pop();
		}
	}
	if (_active_anis.length == 0) {
		clearInterval(_ani_tmr);
	}
}
function animate_base(getter, setter, from, to, dur, interp, unq, unqcheck, onintr = function(proc) { return false; }) {
	var ani = new _ani_obj(getter, setter, from, to, dur, interp, unq, unqcheck, onintr);
	_active_anis.push(ani);
	if (_active_anis.length == 1) {
		_ani_tmr = setInterval(function() {
			_update_animation();
		}, 10);
	}
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

function default_aniunq(ani, obj, prop, pfx) {
	obj[pfx + prop] = ani.fromt;
}
function default_aniunqcheck(ani, obj, prop, pfx) {
	return obj[pfx + prop] == ani.fromt;
}
function animate_property(
	obj, prop, from, to, dur, interp = linear_interp,
	unq = function(ani) { return default_aniunq(ani, obj, prop, '_aniunq_'); },
	checkunq = function(ani) { return default_aniunqcheck(ani, obj, prop, '_aniunq_'); },
	onintr = function(proc) { return false; }
) {
	animate_base(function() {
		return obj[prop];
	}, function(val) {
		obj[prop] = val;
	}, from, to, dur, interp, unq, checkunq, onintr);
}
function animate_property_to(
	obj, prop, to, dur, interp = linear_interp,
	unq = function(ani) { return default_aniunq(ani, obj, prop, '_aniunq_'); },
	checkunq = function(ani) { return default_aniunqcheck(ani, obj, prop, '_aniunq_'); },
	onintr = function(proc) { return false; }
) {
	animate_base(function() {
		return obj[prop];
	}, function(val) {
		obj[prop] = val;
	}, obj[prop], to, dur, interp, unq, checkunq, onintr);
}
function animate_style_property(
	obj, prop, from, to, unit, dur, interp = linear_interp,
	unq = function(ani) { return default_aniunq(ani, obj, prop, '_aniunq_style_'); },
	checkunq = function(ani) { return default_aniunqcheck(ani, obj, prop, '_aniunq_style_'); },
	onintr = function(proc) { return false; }
) {
	animate_base(function() {
		return obj.style[prop];
	}, function(val) {
		obj.style[prop] = val + unit;
	}, from, to, dur, interp, unq, checkunq, onintr);
}
function animate_style_property_to(
	obj, prop, to, unit, dur, interp = linear_interp,
	unq = function(ani) { return default_aniunq(ani, obj, prop, '_aniunq_style_'); },
	checkunq = function(ani) { return default_aniunqcheck(ani, obj, prop, '_aniunq_style_'); },
	onintr = function(proc) { return false; }
) {
	animate_base(function() {
		return obj.style[prop];
	}, function(val) {
		obj.style[prop] = val + unit;
	}, parseFloat(obj.style[prop]), to, dur, interp, unq, checkunq, onintr);
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
