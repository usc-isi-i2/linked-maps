# Problems in Setuping the software

## Repository README.md

1. It should explain how to setup the linked maps project here only. 
2. It should mention the dependencies and installations required including versions.
3. Even if we plan to use Docker finally. I would suggest having this information for devs to install it in their own systems. Right now I can't configure this install.
4. Please explain in which order the README.md inside folder's should be read. This is not mentioned explicitly.

## Line Segmentation README.md issues

1. Program requires Python 2.7 README should explain if it works with Python 3.x. 
2. It Should be made compatible with later versions of Python.
3. pip install osgeo does not work.  `Collecting osgeo Could not find a version that satisfies the requirement osgeo (from versions: ) No matching distribution found for osgeo`  There needs to be alternatives on how to install this.
4. Postgre Server Setup details needs to be given in greater detail.
5. Explain what "edit config.json" means in a step by step manner i.e what can I change and what can't I change while I do the setup.

## Query_and_viz/pre-jena README.md issues

1. Specify which Apache-Jena-Fuseki do I need to install. Do you mean apache-jena-fuseki-3.12.0.tar.gz ? If so please correct this.
2. Instead of asking the user to modify YOURPATH , I think we can make it do this itself. We only need to ask user to move the file to the location and then we can infer the location and thus YOURPATH.
3. The path is in UNIX/MacOS format. Mention that it may need to change for Windows formats.
4. run/configuration don't exist. Mention that we need to make them.
5. java command doesn't work.  `Error: Could not find or load main class org.apache.jena.fuseki.cmd.FusekiCmd` is displayed.

## Query_and_viz/pre-rdf-viz README.md issues

1. This edit is another thing that can be avoided from the user end if we just upload the Apache-Jena-Fuseki with all edits done already.
