# Query and Visualization 
1. Visualize raw maps (without line segmentation)
![](https://github.com/usc-isi-i2/linked-maps/blob/master/0%20-%20Misc/photos/Untitled.png)

How to?
1. Install Node.js
2. Download folder ```Visualize Raw``` to local 
3. Open terminal, navigate to this folder. Run ``` browser-sync start --server --files "*.html, *.json"```

Note. JSON version of shapefile can be exported from QGIS WKT and add the comma at the end of the every  line except last line

2. Visualize RDF on Apache Jena (after line segmentation and model with Karma)
![](https://github.com/usc-isi-i2/linked-maps/blob/master/0%20-%20Misc/photos/jena_visualize.png)

How to?
1. [Set up Apache Jena](https://github.com/usc-isi-i2/linked-maps/tree/master/3%20-%20Query%20and%20Visualization%20(Jena)/Jena%20Setup). Now we will have standard Apache Jena
2. [Add WKT visualization feature](https://github.com/usc-isi-i2/linked-maps/tree/master/3%20-%20Query%20and%20Visualization%20(Jena)/Jena%20Setup)
