/* WGS84 model; Amap expects GCJ-02. coordtransform MIT is bundled alongside. */
(function(root){
  function links(to,from,mode='bus'){
    const url=(base,params)=>base+'?'+new URLSearchParams(params).toString();
    const name=p=>(p.city||'')+' '+p.name.split(' · ')[0];
    if(!Number.isFinite(to.lat)||!Number.isFinite(to.lng)){const query=name(to);return {amap:url('https://uri.amap.com/search',{keyword:query,city:to.city||'',callnative:'0'}),amapApp:url('https://uri.amap.com/search',{keyword:query,city:to.city||'',callnative:'1'}),apple:url('https://maps.apple.com/',{daddr:query,dirflg:({bus:'r',walk:'w',car:'d'})[mode]}),baidu:url('https://api.map.baidu.com/direction',{origin:'我的位置',destination:query,region:to.city||'',mode:({bus:'transit',walk:'walking',car:'driving'})[mode],output:'html',src:'webapp.shitu.travel'})};}
    const amapPoint=p=>{const c=root.coordtransform.wgs84togcj02(p.lng,p.lat);return c.map(n=>n.toFixed(6)).join(',')+','+name(p)};
    const bdPoint=p=>'latlng:'+p.lat+','+p.lng+'|name:'+name(p);
    const amap={to:amapPoint(to),mode,policy:'0',src:'shitu',callnative:'0'};
    if(from)amap.from=amapPoint(from);
    const apple={daddr:name(to),dirflg:({bus:'r',walk:'w',car:'d'})[mode]};
    if(from)apple.saddr=name(from);
    return {
      amap:url('https://uri.amap.com/navigation',amap),
      amapApp:url('https://uri.amap.com/navigation',{...amap,callnative:'1'}),
      apple:url('https://maps.apple.com/',apple),
      baidu:url('https://api.map.baidu.com/direction',{origin:from?bdPoint(from):'我的位置',destination:bdPoint(to),mode:({bus:'transit',walk:'walking',car:'driving'})[mode],region:to.city||'',coord_type:'wgs84',output:'html',src:'webapp.shitu.travel'}),
      osm:'https://www.openstreetmap.org/?mlat='+to.lat+'&mlon='+to.lng+'#map=17/'+to.lat+'/'+to.lng
    };
  }
  root.TravelNavigation={links};
})(typeof window!=='undefined'?window:globalThis);
