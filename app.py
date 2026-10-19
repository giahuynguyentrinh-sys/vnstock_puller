symbols = [
    "AAA", "AAT", "ABR", "ABS", "ABT", "ACB", "ACC", "ACG", "ACL", "ADG", "ADP", "ADS", "AGG", "AGM", "AGR", "AMD",
    "ANV", "APC", "APG", "APH", "ASG", "ASM", "ASP", "AST", "BBT", "BCE", "BCG", "BCM", "BFC", "BHN", "BIC", "BID",
    "BMC", "BMI", "BMP", "BRC", "BSC", "BSI", "BTP", "BKG", "BWE", "C32", "C47", "CCL", "CDC", "CHP", "CIG", "CII",
    "CKG", "CLC", "CLL", "CMG", "CMX", "CNG", "COM", "CRC", "CSM", "CSV", "CTD", "CTF", "CTG", "CTI", "CTR", "CTS",
    "CVT", "D11", "D2D", "DAH", "DAT", "DBC", "DBD", "DBT", "DC4", "DC1", "DCM", "DHA", "DHC", "DHG", "DHM", "DIG",
    "DLG", "DMC", "DPG", "DPM", "DPR", "DRC", "DRH", "DRL", "DSN", "DTA", "DTL", "DTP", "DTT", "DVP", "DXG", "DXS",
    "EIB", "ELC", "EVE", "EVF", "FCM", "FCN", "FDC", "FIR", "FIT", "FLC", "FMC", "FPT", "FRT", "FTS", "GAS", "GDT",
    "GEG", "GEX", "GIL", "GMC", "GMD", "GMH", "GSP", "GTA", "GVR", "HAG", "HAH", "HAP", "HAR", "HAS", "HAX", "HBC",
    "HCD", "HCM", "HDA", "HDC", "HDG", "HDB", "HG1", "HG2", "HGM", "HHV", "HID", "HIP", "HI1", "HJA", "HJT", "HMC",
    "HNG", "HOT", "HPG", "HQC", "HRC", "HSG", "HSL", "HT1", "HTI", "HTL", "HTN", "HTV", "HU1", "HUB", "HU4", "HVN",
    "HVX", "HYT", "IJC", "IMP", "ITA", "ITC", "ITD", "JVC", "KBC", "KDC", "KDH", "KHG", "KH1", "KMR", "KOS", "KPF",
    "KSB", "L10", "LAF", "LBM", "LCG", "LDG", "LEC", "LGC", "LGL", "LHG", "LI4", "LIX", "LM8", "LPB", "LSS", "MBB",
    "MCD", "MCG", "MCH", "MCM", "MCP", "MDG", "MIG", "MIB", "MSB", "MSN", "MWG", "NAB", "NAF", "NBB", "NCT", "NFC",
    "NHG", "NLG", "NMC", "NNG", "NNT", "NO1", "NPG", "NPL", "NPM", "NTH", "NTL", "NT2", "NTP", "NVL", "NVT", "OCB",
    "OGC", "OPC", "ORS", "PAC", "PAN", "PC1", "PDN", "PDR", "PET", "PGC", "PGD", "PGI", "PGV", "PHC", "PHR", "PIT",
    "PJT", "PLX", "PMC", "PMG", "PNJ", "POM", "POW", "PPC", "PTB", "PTC", "PTL", "PVD", "PVT", "PXI", "PXS", "PXT",
    "QBS", "QCG", "RAL", "RDP", "REE", "S4A", "SAB", "SAM", "SAV", "SBA", "SBT", "SBV", "SC5", "SCS", "SFC", "SFG",
    "SGN", "SGR", "SGT", "SHA", "SHB", "SHI", "SHP", "SIP", "SJD", "SJF", "SJS", "SKG", "SMB", "SMC", "SPM", "SRF",
    "SSB", "SSC", "SSI", "ST8", "STB", "STG", "STK", "SVT", "SZC", "SZL", "TAC", "TBC", "TCB", "TCD", "TCH", "TCL",
    "TCM", "TCO", "TCR", "TCT", "TDC", "TDH", "TDG", "TDM", "TD1", "TEG", "THG", "THI", "TIP", "TIX", "TLD", "TLG",
    "TLH", "TMP", "TMS", "TNH", "TN1", "TNC", "TNH", "TNI", "TNT", "TPB", "TPC", "TRA", "TRC", "TS4", "TSC", "TTA",
    "TTE", "TTF", "TVT", "TV2", "TYN", "UIC", "VAF", "VCA", "VCB", "VCF", "VCG", "VCI", "VD1", "VMD", "VND", "VNE",
    "VNG", "VNL", "VNM", "VNS", "VOS", "VPB", "VPD", "VPG", "VPH", "VPI", "VRC", "VRE", "VSC", "VSH", "VSI", "VTB",
    "VTO", "YBM", "YEG"
] 


# Làm sạch danh sách symbols
symbols_clean = sorted(set(symbols))

# Kiểm tra những mã bị trùng
seen = set()
duplicates = []

for symbol in symbols:
    if symbol in seen and symbol not in duplicates:
        duplicates.append(symbol)
    seen.add(symbol)

print("Các mã trùng:", duplicates)
print("Số mã ban đầu:", len(symbols))
print("Số mã sau khi làm sạch:", len(symbols_clean))

# In danh sách hoàn chỉnh để sao chép
print("\nsymbols = [")
for i in range(0, len(symbols_clean), 8):
    print("    " + ", ".join(
        repr(s) for s in symbols_clean[i:i + 8]
    ) + ",")
print("]")
