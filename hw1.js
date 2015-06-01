var mod = angular.module("homework01", []);

mod.controller("mainController", function(){
	var self = this;

	self.themeSelection = "themeRed";

	this.checkboxValue = true;

	this.mainList = {"Green":"#00FF00","Red":"#FF0000","Blue":"#0000FF"};

	self.getTheme = function(shade){
		if (self.themeSelection === "themeBlue"){
			return (shade === "shade1") ? "shade1Blue" : "shade2Blue";
		}
		if (self.themeSelection === "themeRed"){
			return (shade === "shade1") ? "shade1Red" : "shade2Red";
		}
		if (self.themeSelection === "themeGreen"){
			return (shade === "shade1") ? "shade1Green" : "shade2Green";
		}
	};

	self.placeholder = "Lorem ipsum dolor sit amet, cu pro error scaevola, cu usu ferri quando liberavisse. Ne vix epicuri urbanitas, vix modus vocent omittantur no. Ei nec odio dolorum constituam, per ex bonorum docendi, vis paulo offendit te. Mutat legere mea ex, qui et tractatos dissentiet, vim liber albucius volutpat ad. Ex eos prompta maluisset, mea modus oratio diceret at. Posidonium accommodare an vim, ea sed iriure alienum. No tincidunt repudiandae cum. At eum deleniti suavitate. Ei reque assueverit temporibus vis, nec no scaevola legendos reprimique. Qui cu mazim dolorem praesent, ad labitur appareat explicari his, ius te amet evertitur scribentur. Porro discere te pri. Ea nulla oblique consequat mea, posse suscipit salutandi te pro. Vide scribentur dissentiet sea at. Eos eu quando soleat sadipscing, in nam dolores petentium, meis porro nam ad.Epicurei explicari qui in, aperiri impedit omnesque vel te, cu his equidem volutpat. Hinc mazim vel ut, delicata mediocritatem mel te. Sed labitur fuisset id, qui erant dolores mediocritatem ex, eius insolens pertinacia duo id. Quo mundi dolores vivendum ex, vel in accommodare consequuntur. Te ullum nominati explicari usu, omnium maiestatis vel ei. In labores accumsan verterem per. Et pro veri solum, expetenda consequat usu ne. Ei qui ancillae delectus, eu mel soleat causae atomorum. Oporteat percipitur qui ne. Minim antiopam scribentur in his." 

});
