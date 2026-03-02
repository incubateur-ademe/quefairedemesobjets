/* global ol */
"use strict"

// =============================================================================
// UPSTREAM: verbatim copy of Django's OLMapWidget.js
// Source: django/contrib/gis/static/gis/js/OLMapWidget.js
// Django version: 6.0.2
//
// To upgrade: replace everything between UPSTREAM START and UPSTREAM END with
// the new version of OLMapWidget.js, then verify the QFDMO overrides below
// still apply cleanly (check: defaultCenter, serializeFeatures,
// createInteractions, and the constructor's this.ready = true line).
// =============================================================================
// UPSTREAM START

class GeometryTypeControl extends ol.control.Control {
  constructor(opt_options) {
    const options = opt_options || {}
    const element = document.createElement("div")
    element.className =
      "switch-type type-" + options.type + " ol-control ol-unselectable"
    if (options.active) {
      element.classList.add("type-active")
    }
    super({ element: element, target: options.target })
    const self = this
    const switchType = function (e) {
      e.preventDefault()
      if (options.widget.currentGeometryType !== self) {
        options.widget.map.removeInteraction(options.widget.interactions.draw)
        options.widget.interactions.draw = new ol.interaction.Draw({
          features: options.widget.featureCollection,
          type: options.type,
        })
        options.widget.map.addInteraction(options.widget.interactions.draw)
        options.widget.currentGeometryType.element.classList.remove("type-active")
        options.widget.currentGeometryType = self
        element.classList.add("type-active")
      }
    }
    element.addEventListener("click", switchType, false)
    element.addEventListener("touchstart", switchType, false)
  }
}

class MapWidget {
  constructor(options) {
    this.map = null
    this.interactions = { draw: null, modify: null }
    this.typeChoices = false
    this.ready = false
    this.options = {
      default_lat: 0,
      default_lon: 0,
      default_zoom: 12,
      is_collection:
        options.geom_name.includes("Multi") || options.geom_name.includes("Collection"),
    }
    for (const property in options) {
      if (Object.hasOwn(options, property)) {
        this.options[property] = options[property]
      }
    }
    const base_layer = options.base_layer
    if (typeof base_layer === "string" && base_layer in MapWidget.layerBuilder) {
      this.baseLayer = MapWidget.layerBuilder[base_layer]()
    } else if (base_layer && typeof base_layer !== "string") {
      this.baseLayer = base_layer
    } else {
      this.baseLayer = MapWidget.layerBuilder.osm()
    }
    this.map = this.createMap()
    this.featureCollection = new ol.Collection()
    this.featureOverlay = new ol.layer.Vector({
      map: this.map,
      source: new ol.source.Vector({
        features: this.featureCollection,
        useSpatialIndex: false,
      }),
      updateWhileAnimating: true,
      updateWhileInteracting: true,
    })
    const self = this
    this.featureCollection.on("add", function (event) {
      const feature = event.element
      feature.on("change", function () {
        self.serializeFeatures()
      })
      if (self.ready) {
        self.serializeFeatures()
        if (!self.options.is_collection) {
          self.disableDrawing()
        }
      }
    })
    const initial_value = document.getElementById(this.options.id).value
    if (initial_value) {
      const jsonFormat = new ol.format.GeoJSON()
      const features = jsonFormat.readFeatures(
        '{"type": "Feature", "geometry": ' + initial_value + "}",
      )
      const extent = ol.extent.createEmpty()
      features.forEach(function (feature) {
        this.featureOverlay.getSource().addFeature(feature)
        ol.extent.extend(extent, feature.getGeometry().getExtent())
      }, this)
      this.map.getView().fit(extent, { minResolution: 1 })
    } else {
      this.map.getView().setCenter(this.defaultCenter())
    }
    this.createInteractions()
    if (initial_value && !this.options.is_collection) {
      this.disableDrawing()
    }
    const clearNode = document.getElementById(this.map.getTarget()).nextElementSibling
    if (clearNode.classList.contains("clear_features")) {
      clearNode.querySelector("a").addEventListener("click", (ev) => {
        ev.preventDefault()
        self.clearFeatures()
      })
    }
    this.ready = true

    // ↓ QFDMO patch 3 — see below
    this._qfdmoRegister()
  }

  createMap() {
    return new ol.Map({
      target: this.options.map_id,
      layers: [this.baseLayer],
      view: new ol.View({ zoom: this.options.default_zoom }),
    })
  }

  createInteractions() {
    this.interactions.modify = new ol.interaction.Modify({
      features: this.featureCollection,
      deleteCondition: function (event) {
        return (
          ol.events.condition.shiftKeyOnly(event) &&
          ol.events.condition.singleClick(event)
        )
      },
    })
    let geomType = this.options.geom_name
    if (geomType === "Geometry" || geomType === "GeometryCollection") {
      geomType = "Point"
      this.currentGeometryType = new GeometryTypeControl({
        widget: this,
        type: "Point",
        active: true,
      })
      this.map.addControl(this.currentGeometryType)
      this.map.addControl(
        new GeometryTypeControl({ widget: this, type: "LineString", active: false }),
      )
      this.map.addControl(
        new GeometryTypeControl({ widget: this, type: "Polygon", active: false }),
      )
      this.typeChoices = true
    }
    this.interactions.draw = new ol.interaction.Draw({
      features: this.featureCollection,
      type: geomType,
    })
    this.map.addInteraction(this.interactions.draw)
    this.map.addInteraction(this.interactions.modify)

    // ↓ QFDMO patch 1+2 — see below
    this._qfdmoPostInteractions()
  }

  defaultCenter() {
    const center = [this.options.default_lon, this.options.default_lat]
    if (this.options.map_srid) {
      return ol.proj.transform(center, "EPSG:4326", this.map.getView().getProjection())
    }
    return center
  }

  enableDrawing() {
    this.interactions.draw.setActive(true)
    if (this.typeChoices) {
      const divs = document.getElementsByClassName("switch-type")
      for (let i = 0; i !== divs.length; i++) {
        divs[i].style.visibility = "visible"
      }
    }
  }

  disableDrawing() {
    if (this.interactions.draw) {
      this.interactions.draw.setActive(false)
      if (this.typeChoices) {
        const divs = document.getElementsByClassName("switch-type")
        for (let i = 0; i !== divs.length; i++) {
          divs[i].style.visibility = "hidden"
        }
      }
    }
  }

  clearFeatures() {
    this.featureCollection.clear()
    document.getElementById(this.options.id).value = ""
    this.enableDrawing()
  }

  serializeFeatures() {
    let geometry = null
    const features = this.featureOverlay.getSource().getFeatures()
    if (this.options.is_collection) {
      if (this.options.geom_name === "GeometryCollection") {
        const geometries = []
        for (let i = 0; i < features.length; i++) {
          geometries.push(features[i].getGeometry())
        }
        geometry = new ol.geom.GeometryCollection(geometries)
      } else {
        geometry = features[0].getGeometry().clone()
        for (let j = 1; j < features.length; j++) {
          switch (geometry.getType()) {
            case "MultiPoint":
              geometry.appendPoint(features[j].getGeometry().getPoint(0))
              break
            case "MultiLineString":
              geometry.appendLineString(features[j].getGeometry().getLineString(0))
              break
            case "MultiPolygon":
              geometry.appendPolygon(features[j].getGeometry().getPolygon(0))
          }
        }
      }
    } else if (features[0]) {
      geometry = features[0].getGeometry()
    }
    // ↓ QFDMO patch 1 — projection options injected here
    document.getElementById(this.options.id).value =
      new ol.format.GeoJSON().writeGeometry(geometry, this._qfdmoProjOptions())
  }
}

MapWidget.layerBuilder = {
  nasaWorldview: () =>
    new ol.layer.Tile({
      source: new ol.source.XYZ({
        attributions: "NASA Worldview",
        maxZoom: 8,
        url:
          "https://map1{a-c}.vis.earthdata.nasa.gov/wmts-webmerc/" +
          "BlueMarble_ShadedRelief_Bathymetry/default/%7BTime%7D/" +
          "GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg",
      }),
    }),
  osm: () => new ol.layer.Tile({ source: new ol.source.OSM() }),
}

function initMapWidgetInSection(section) {
  const maps = []
  section.querySelectorAll(".dj_map_wrapper").forEach((wrapper) => {
    if (wrapper.id.includes("__prefix__")) {
      return
    }
    const textarea_id = wrapper.querySelector("textarea").id
    const options_script = wrapper.querySelector(
      `script#${textarea_id}_mapwidget_options`,
    )
    const options = JSON.parse(options_script.textContent)
    options.id = textarea_id
    options.map_id = wrapper.querySelector(".dj_map").id
    maps.push(new MapWidget(options))
  })
  return maps
}

document.addEventListener("DOMContentLoaded", () => {
  initMapWidgetInSection(document)
  document.addEventListener("formset:added", (ev) => {
    initMapWidgetInSection((ev as CustomEvent).target as Element)
  })
})

// UPSTREAM END
// =============================================================================
// QFDMO OVERRIDES
//
// Three hook methods added to MapWidget.prototype. The upstream code calls them
// via clearly marked one-liners (↓ QFDMO patch N) so the diff to upstream is
// minimal and immediately visible on upgrade.
//
//   Patch 1 — Projection
//     _qfdmoProjOptions() returns {dataProjection, featureProjection} when
//     dataset_epsg / map_epsg are present in widget attrs (set by
//     CustomOSMWidget.__init__ in widgets.py), falling back to {} otherwise.
//     _qfdmoPostInteractions() re-loads the initial value with those options.
//     defaultCenter is also overridden to use the configured projections.
//
//   Patch 2 — Style
//     _qfdmoPostInteractions() also applies an optional `style` attr to the
//     featureOverlay, draw and modify interactions.
//
//   Patch 3 — Registry
//     _qfdmoRegister() stores each instance on window.geodjangoWidgets[id] so
//     the search template (custom-openlayers-with-search.html) can find it.
//
// When upgrading Django: replace the UPSTREAM block, then look for the
// "↓ QFDMO patch" markers to confirm the call sites are still correct.
// =============================================================================

// Patch 1: helper returning GeoJSON projection options when configured
MapWidget.prototype._qfdmoProjOptions = function () {
  if (this.options.dataset_epsg && this.options.map_epsg) {
    return {
      dataProjection: this.options.dataset_epsg,
      featureProjection: this.options.map_epsg,
    }
  }
  return {}
}

// Patch 1: override defaultCenter to use widget-configured projections
MapWidget.prototype.defaultCenter = function () {
  const center = [this.options.default_lon, this.options.default_lat]
  if (this.options.dataset_epsg && this.options.map_epsg) {
    return ol.proj.transform(center, this.options.dataset_epsg, this.options.map_epsg)
  }
  // Upstream fallback
  if (this.options.map_srid) {
    return ol.proj.transform(center, "EPSG:4326", this.map.getView().getProjection())
  }
  return center
}

// Patch 1+2: called at the end of createInteractions()
MapWidget.prototype._qfdmoPostInteractions = function () {
  // Patch 2: apply custom OL style if provided
  if (this.options.style) {
    this.interactions.draw.setStyle(this.options.style)
    this.interactions.modify.setStyle(this.options.style)
    this.featureOverlay.setStyle(this.options.style)
  }

  // Patch 1: re-load initial value with correct projections
  // (upstream read it without projection options)
  if (!this.options.dataset_epsg || !this.options.map_epsg) {
    return
  }
  const initial_value = document.getElementById(this.options.id).value
  if (!initial_value) {
    return
  }
  this.featureOverlay.getSource().clear()
  const features = new ol.format.GeoJSON().readFeatures(
    '{"type": "Feature", "geometry": ' + initial_value + "}",
    this._qfdmoProjOptions(),
  )
  const extent = ol.extent.createEmpty()
  features.forEach((feature) => {
    this.featureOverlay.getSource().addFeature(feature)
    ol.extent.extend(extent, feature.getGeometry().getExtent())
  })
  this.map.getView().fit(extent, { minResolution: 1 })
}

// Patch 3: register instance by textarea ID for use in templates
MapWidget.prototype._qfdmoRegister = function () {
  if (!window.geodjangoWidgets) {
    window.geodjangoWidgets = {}
  }
  window.geodjangoWidgets[this.options.id] = this
}
