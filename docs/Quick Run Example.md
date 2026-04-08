Quick Run Example.md



-------   

## Quick run example (after cloning on your laptop)

### Create virtualenv and activate:

python3 -m venv venv  
source venv/bin/activate  

### Install dependencies:

pip install -r requirements.txt

### If libclang is not auto-found, set it in the script (see README).

---   

### Run batch analysis:

python refined_cognitive_load.py --batch examples/ --weights weights.json --out results.csv

---   

### Optional sensitivity:

python refined_cognitive_load.py --batch examples/ --weights weights.json --sensitivity --out-dir plots/

-------   

