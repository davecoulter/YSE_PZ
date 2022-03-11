// general paperscript code for drawing

var hitOptions = {
    segments: true,
    stroke: true,
    fill: true,
    tolerance: 3
};


function onMouseDown(event) {
    var allItems = project.getItems({class:Path})
    var hitResult = project.hitTest(event.point, hitOptions);

    // if someone selected a field on a down click, then select it
    for (i=0; i < allItems.length; i++) {
        if (allItems[i].contains(event.point))  {
            item = allItems[i];
            field_pk = item.name.split("_")[1].trim();
            field_clicked(field_pk);
        }
    }
}

// functions for drawing fields
function paper_draw_field(verts,rowID,rowState) {

    var observed = rowState.toString().toLowerCase().trim() === 'true';
    //var rectangle = new Rectangle(new Point(verts[0]), new Point(verts[1]));
    //var path = new Path.Rectangle(rectangle);
    var path = new Path({
        segments: [verts[0], verts[1], verts[2], verts[3], verts[0]],
        selected: false
    });
    path.name = 'F_'+rowID.toString();
    path.strokeCap = 'square';
    var telColor = '#3182bd';
    var obsOpacity = 0.7



    if (observed) {
       path.fillColor = telColor;
       path.opacity = obsOpacity

    } else {
       path.fillColor = null;
       path.opacity = 1.;
       path.strokeColor = telColor;
       path.strokeWidth = 2;
    }
    globals.globalPaths[rowID] = path;

}

function paper_update_field(rowID,rowState) {
    var observed = rowState.toString().toLowerCase().trim() === 'true';
    var path = globals.globalPaths[rowID];
    var telColor = '#3182bd';
    var obsOpacity = 0.7

    if (observed) {
        path.fillColor = telColor;
        path.opacity = obsOpacity
     } else {
        path.fillColor = null;
        path.opacity = 1.;
        path.strokeColor = telColor;
        path.strokeWidth = 2;
     }
     globals.globalPaths[rowID] = path;
}



function paper_draw_background() {
    var raster = new Raster('backgroundSky');
    raster.size = paper.view.viewSize;
    raster.position = paper.view.center;
}

function paper_draw_contours(verts) {

    for (i = 0; i < verts[0].length; i++) {

        var point_ul = new Point(verts[0][i],verts[1][i]);
        var point_lr = new Point(verts[2][i],verts[3][i]);
        shade_super_cell(point_ul,point_lr,verts[4][i]);
    }
}



function shade_super_cell(p_ul,p_lr,prob) {
    var rectangle = new Rectangle(p_ul, p_lr);
    var path = new Path.Rectangle(rectangle);
    path.strokeWidth = 2.;
    path.fillColor = new Color(prob);
    path.sendToBack();
    //path.strokeColor = Color.random();
}


function paper_select_all_fields() {

    // get all the path items (target fields)
    var pathItems = project.getItems({
        class: Path
    })

    // turn this into a group
    fieldsGroup = new Group(pathItems);

    // toggling selection
    if (fieldsGroup.selected) {
        fieldsGroup.selected = false;
    } else {
        fieldsGroup.selected = true;
    }
    // now what?
    //console.log(fieldsGroup);
}


function paper_apply_field_changes() {
    alert('work in progress')

}

function paper_cancel_field_changes() {
    location.reload();
}






// global stuff for linking js and paperscript
globals.paper_draw_field = paper_draw_field;
globals.paper_update_field = paper_update_field;
globals.paper_draw_contours = paper_draw_contours;
globals.paper_draw_background = paper_draw_background;
globals.paper_select_all_fields = paper_select_all_fields;
globals.paper_apply_field_changes = paper_apply_field_changes;
globals.paper_cancel_field_changes = paper_cancel_field_changes;
