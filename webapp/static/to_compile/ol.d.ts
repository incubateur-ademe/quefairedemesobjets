// Ambient declaration for the OpenLayers global loaded by Django's GIS widget.
// The full OL type package (@types/ol) is not installed; this minimal shim is
// sufficient for TypeScript to compile controller code that uses `ol` as a global.
declare const ol: any
