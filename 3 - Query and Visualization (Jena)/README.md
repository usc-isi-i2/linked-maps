# Query and Visualization 
### Visualize raw maps (without line segmentation)
![](https://github.com/usc-isi-i2/linked-maps/blob/master/0%20-%20Misc/photos/Untitled.png)

How to?
1. Install Node.js
2. Download folder ```Visualize Raw``` to local 
3. Open terminal, navigate to this folder. Run ``` browser-sync start --server --files "*.html, *.json"```

We can use scroll bar to visualize maps from time to time.

Note. JSON version of shapefile can be exported from QGIS WKT and add the comma at the end of the every  line except last line

### Visualize RDF on Apache Jena (after line segmentation and model with Karma)
Result from query 1
![](https://github.com/usc-isi-i2/linked-maps/blob/master/0%20-%20Misc/photos/jena_visualize.png)
Result from query 2
![](https://github.com/usc-isi-i2/linked-maps/blob/master/0%20-%20Misc/photos/jena_visulize_one_tripple.png)
How to?
1. [Set up Apache Jena](https://github.com/usc-isi-i2/linked-maps/tree/master/3%20-%20Query%20and%20Visualization%20(Jena)/Jena%20Setup). Now we will have standard Apache Jena
2. [Add WKT visualization feature](https://github.com/usc-isi-i2/linked-maps/tree/master/3%20-%20Query%20and%20Visualization%20(Jena)/Visualize%20RDF). This will create add-on feature to visualize WKT with Google Map on Jena

