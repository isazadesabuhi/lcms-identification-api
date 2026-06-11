from app.services.csv_parser import parse_mzmine_quant_csv


features = parse_mzmine_quant_csv(
    "data/unknown/neg/NEG_fbmn_quant.csv",
    ion_mode="NEG"
)

print("Features detected:", len(features))
print("First feature:")
print(features[0])