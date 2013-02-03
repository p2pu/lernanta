

Lernanta Stlye Guide
===================
All of the elements in this document are customized for p2pu. Please reference this to create a p2pu styled page.

Template Flow
------------------

 * All pages include `templates/base.html`
 * All pages also include `templates/_footer.html`
 * Most pages include `templates/schools/footer.html`
 * Most pages include the type base.html `templates/learn/base.html`
 * Then the individual page `templates/learn/learn.html`

Example: `templates/learn/learn.html`

 * includes `templates/learn/base.html`
 * and `templates/base.html`
 * and `templates/_footer.html`
 * and `templates/schools/footer.html`

For the most part, you should only really be editing an individual page or a section's base.html file
Layouts are standard sitewide


 Common Scaffolding Elements
-------------------

 * Reference Standard [Bootstrap Scaffolding](http://twitter.github.com/bootstrap/scaffolding.html)
 
 
 * Common Layout Elements:
   * Used only once per content block 
   * `<div class="container"></div>` One 'column' fixed page layout
   * `<div class="container-fluid"></div>` Two  'column' fluid layout used for sidebar navigation list links

 * Grid System:
    * Used within `class="container" or "container-fluid` elements
    * (Use `<div class="fluid-grid">` to reset grid)
    * 12 columns default. Sum of span columns `<div class="span(COLUMNS)">` needs to equal 12
        * `<div class="row-fluid">`
        * `<div class="span4">`


Well Classes- changes based on containing element (thumbnails)

 * `<div class="well"></div>`
 * `<div class="well well-large"></div>`
 
Text

 * Reference Standard [Bootstrap Typography](http://twitter.github.com/bootstrap/base-css.html#typography)
 * Uses [Trunc8](https://github.com/rviscomi/trunk8) to truncate lines semantically 
    * `<span class="truncate-to-1-line">TEXT</span>`
    * `<span class="truncate-to-3-lines">TEXT</span>`
    * Works up to 10 lines
    
Images
 
 * Reference Standard [Bootstrap Images](http://twitter.github.com/bootstrap/base-css.html#images)
 * Consider containing in a `<div class="well">`
 
Buttons

* btn - in general should be used in an `<a>` not `<button>`
* `<a href='#' class="btn btn-large btn-olive">BUTTON_TEXT</a>`
  * Size Classes
      * btn-large
      * btn-skinny
      * btn-short
  * Color Classes
      * btn-olive
      * btn-apricot
      * btn-cyan


Standard Page Title

 * `<h1>Page Title</h1>`
 * `<h1><small>Page Sub-Title</small></h1>`
 
     
      
P2PU Site Specific Elements
--------------------------
      
Breadcrumbs - breadcrumbs on a page get injected into a `<ul class="breadcrumbs">` on the main base.html

 * `<li><span class="divider">&rsaquo;</span><a href="BREADCRUMB_URL">BREADCRUMB_TITLE</a></li>`
 * Breadcrumb Actions are not list items. Instead use:
   * `<a class="btn btn-skinny btn-apricot" href="#">ACTION_TEXT</a>`
   
Sidebar Navigation List

 ```html
 <div class="span3">
   <ul class 
 </div>
 ```

Course Cards - Overridden bootstrap thumbnail currently used for displaying courses


```html
<ul class="thumbnails">
  <li class="span4">
    <div class="thumbnail">
      <a href="PROJECT_URL">
      <img src="IMAGE_URL" width="203" height="125" />
      </a>
    <div class="caption">
      <h3><a href="PROJECT_URL"><span class="truncate-to-2-lines">TITLE</span></a></h3>
      <p><span class="truncate-to-3-lines">DESCRIPTION</span></p>
    </div>
    <div class="well well-large">
      <dl>
        <dt><span class="label">BOTTOM_LEFT_LABEL</span></dt>
          <dd><span class="badge">BOTTOM_LEFT_VALUE</span></dd>
      </dl>
      <dl>
        <dt><span class="label">BOTTOM_CENTER_LABEL</span></dt>
          <dd><span class="badge">BOTTOM_CENTER_VALUE</span></dd>
      </dl>
      <dl>
        <dt><span class="label">BOTTOM_RIGHT_LABEL</span></dt>
          <dd><span class="badge">BOTTOM_RIGHT_VALUE</span></dd>
      </dl>
    </div>
  </li>
</ul>
```
    



