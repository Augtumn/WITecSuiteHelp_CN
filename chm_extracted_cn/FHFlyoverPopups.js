var offsetfromcursorX=-20
var offsetfromcursorY=0
var offsetdivfrompointerX=10
var offsetdivfrompointerY=16

document.write('<img id="arrowhead" src="">')

var ie=document.all
var ns6=document.getElementById && !document.all
var opera=false;
var showpopup=false;
var enablearrowhead=0
if (ie||ns6)
var popupBox=document.all? document.all["FHFlyoverPopupStyle"] : document.getElementById? document.getElementById("FHFlyoverPopupStyle") : ""
var popupArrow=document.all? document.all["arrowhead"] : document.getElementById? document.getElementById("arrowhead") : ""

var arrowheadimg=["Images/LongArrowDownGray.gif", "Images/LongArrowUpGray.gif"]

if (navigator.userAgent.indexOf("Opera")!=-1)
 {opera=true;}

function ietruebody()
{return (document.compatMode && document.compatMode!="BackCompat")? document.documentElement : document.body}

function FHDisplayFlyoverPopup(obj, iWidth)
{
  popupBox=document.all? document.all[obj] : document.getElementById? document.getElementById(obj) : ""
  if (ns6||ie)
  {
    if (typeof iWidth!="undefined") 
      {popupBox.style.width=iWidth+"px"}
    showpopup=true
    return false
  }
}

function FHPositionTheFlyoverPopup(e)
{
  if (showpopup)
  {
    var nondefaultpos=false
    var curX=(ns6)?e.pageX : event.clientX+ietruebody().scrollLeft;
    var curY=(ns6)?e.pageY : event.clientY+ietruebody().scrollTop;
    var winwidth=ie&&!window.opera? ietruebody().clientWidth : window.innerWidth-20
    var winheight=ie&&!window.opera? ietruebody().clientHeight : window.innerHeight-20
    var rightedge=ie&&!window.opera? winwidth-event.clientX-offsetfromcursorX : winwidth-e.clientX-offsetfromcursorX
    var bottomedge=ie&&!window.opera? winheight-event.clientY-offsetfromcursorY : winheight-e.clientY-offsetfromcursorY
    var leftedge=(offsetfromcursorX<0)? offsetfromcursorX*(-1) : -1000
    if (rightedge<popupBox.offsetWidth)
    {
      i = curX-popupBox.offsetWidth;
      if (i<0)
        {i = 0}
      popupBox.style.left=i+"px"
      popupArrow.style.left=curX+offsetfromcursorX+"px"
      nondefaultpos=true
    }
    else if (curX<leftedge)
    {popupBox.style.left="5px"}
    else
    {  
      i = curX+offsetfromcursorX-offsetdivfrompointerX;
      if (i<0)
        {i = 0}
      popupBox.style.left=i+"px"
      popupArrow.style.left=curX+offsetfromcursorX+"px"
    }

    if (bottomedge<popupBox.offsetHeight)
    {
      nondefaultpos=true
      popupArrow.src=arrowheadimg[0];
      if (opera || ns6)
        {popupBox.style.top=curY-popupBox.offsetHeight-offsetdivfrompointerY-offsetfromcursorY+1+"px";}
      else
        {popupBox.style.top=curY-popupBox.offsetHeight-offsetdivfrompointerY-offsetfromcursorY+6+"px";}

      popupArrow.style.top=curY+popupBox.style.height-offsetdivfrompointerY-offsetfromcursorY+"px"
    }
    else
    {
      popupArrow.src=arrowheadimg[1];
      popupBox.style.top=curY+offsetfromcursorY+offsetdivfrompointerY+"px"
      popupArrow.style.top=curY+offsetfromcursorY+"px"
    }
    popupBox.style.visibility="visible"

    if (enablearrowhead)
      popupArrow.style.visibility="visible"
    else
      popupArrow.style.visibility="hidden"
  }
}

function FHHideFlyoverPopup()
{
  if (ns6||ie)
  {
    showpopup=false
    popupBox.style.visibility="hidden"
    popupArrow.style.visibility="hidden"
    popupBox.style.left="-1000px"
    popupBox.style.width=''
  }
}

document.onmousemove=FHPositionTheFlyoverPopup