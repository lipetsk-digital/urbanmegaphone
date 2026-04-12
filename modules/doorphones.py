# ============================================
# Module: Load doorphones data and assign to buildings
# ============================================

# Modules import
# ============================================

# Standart modules
from pathlib import Path # Crossplatform pathing
import pandas as pd # For tables of data

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition


# ============================================
# Load FIAS codes of buildings with doorphones and assign flags to gdfBuildings
# ============================================
def LoadDoorphones():

    env.logger.info("Load doorphones data...")

    # Initialize doorphone field in gdfBuildings (0 = no doorphone)
    env.gdfBuildings['doorphone'] = 0

    # Load FIAS codes from FACT folder
    factFiles = list(Path('.', cfg.folderDOORPHONES_FACT).glob("*.txt", case_sensitive=False))
    dfList = []
    for file in factFiles:
        env.logger.debug("Load doorphones FACT: {file}", file=file)
        df = pd.read_csv(file, header=None, names=['fias'], dtype=str, skip_blank_lines=True)
        df['fias'] = df['fias'].str.strip()
        df = df[df['fias'] != '']
        dfList.append(df)
    if dfList:
        pdFact = pd.concat(dfList, ignore_index=True).drop_duplicates()
    else:
        pdFact = pd.DataFrame(columns=['fias'])
    env.logger.success("{} FIAS codes loaded from FACT files", len(pdFact.index))

    # Load FIAS codes from PLAN folder
    planFiles = list(Path('.', cfg.folderDOORPHONES_PLAN).glob("*.txt", case_sensitive=False))
    dfList = []
    for file in planFiles:
        env.logger.debug("Load doorphones PLAN: {file}", file=file)
        df = pd.read_csv(file, header=None, names=['fias'], dtype=str, skip_blank_lines=True)
        df['fias'] = df['fias'].str.strip()
        df = df[df['fias'] != '']
        dfList.append(df)
    if dfList:
        pdPlan = pd.concat(dfList, ignore_index=True).drop_duplicates()
    else:
        pdPlan = pd.DataFrame(columns=['fias'])
    env.logger.success("{} FIAS codes loaded from PLAN files", len(pdPlan.index))

    # Match PLAN FIAS codes with gdfBuildings and warn about unmatched
    planMatched = pdPlan.merge(env.gdfBuildings[['fias', 'UIB']], on='fias', how='left')
    planUnmatched = planMatched[planMatched['UIB'].isna()]
    for row in planUnmatched.itertuples():
        env.logger.warning("PLAN doorphone FIAS not found in buildings: {}", row.fias)
    planMatched = planMatched.dropna(subset=['UIB'])

    # Assign doorphone = 2 (plan) for matched PLAN buildings
    env.gdfBuildings.loc[env.gdfBuildings['fias'].isin(planMatched['fias']), 'doorphone'] = 2

    # Match FACT FIAS codes with gdfBuildings and warn about unmatched
    factMatched = pdFact.merge(env.gdfBuildings[['fias', 'UIB']], on='fias', how='left')
    factUnmatched = factMatched[factMatched['UIB'].isna()]
    for row in factUnmatched.itertuples():
        env.logger.warning("FACT doorphone FIAS not found in buildings: {}", row.fias)
    factMatched = factMatched.dropna(subset=['UIB'])

    # Assign doorphone = 1 (fact) for matched FACT buildings (overrides plan)
    env.gdfBuildings.loc[env.gdfBuildings['fias'].isin(factMatched['fias']), 'doorphone'] = 1

    # Duplicate doorphone values into env.buildings shared array
    for b in env.gdfBuildings[env.gdfBuildings['doorphone'] > 0].itertuples():
        env.buildings[int(b.UIB * env.sizeBuilding + 5)] = int(b.doorphone)

    countFact = len(env.gdfBuildings[env.gdfBuildings['doorphone'] == 1].index)
    countPlan = len(env.gdfBuildings[env.gdfBuildings['doorphone'] == 2].index)
    env.logger.success("{} buildings with doorphones (fact), {} buildings with doorphones (plan)", countFact, countPlan)
