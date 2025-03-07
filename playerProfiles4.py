import streamlit as st
import numpy as np
import requests
import pandas as pd
import ssl, os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ssl._create_default_https_context = ssl._create_unverified_context


st.set_page_config(
    page_title="MLB DW Player Pages",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DATA LOAD BLOCK
base_dir = os.path.dirname(__file__)
file_path = os.path.join(base_dir, 'Data')
hprojections = pd.read_csv(f'{file_path}/ja_h.csv')
pprojections = pd.read_csv(f'{file_path}/ja_p.csv')
fscores_h = pd.read_csv(f'{file_path}/fScoresHit.csv')
hitlogs = pd.read_csv(f'{file_path}/hitdb25.csv').sort_values(by='game_date', ascending=False)
pitchlogs = pd.read_csv(f'{file_path}/pitdb25.csv').sort_values(by='game_date', ascending=False)

ids_zip = pd.read_csv(f'{file_path}/zips_ids.csv')
ids_zip['MLBID'] = ids_zip['MLBID'].astype(str)
ids_zip['FGID'] = ids_zip['FGID'].astype(str)
fscores_hit = pd.read_csv(f'{file_path}/fscoresHit.csv')
fscores_pitch = pd.read_csv(f'{file_path}/fscoresPitch.csv')

hskills = pd.read_csv(f'{file_path}/HitterSkillData.csv')
pitchskills = pd.read_csv(f'{file_path}/PitcherSkillData.csv')

milbsav25 = pd.read_csv(f'{file_path}/hit_minors_advanced25.csv')
milbsav25['Year']='2025'
milbsav24 = pd.read_csv(f'{file_path}/hit_minors_advanced24.csv')
milbsav24['Year']='2024'
milbsav = pd.concat([milbsav25,milbsav24])

try:
    pmix_mlb_24 = pd.read_csv(f'{file_path}/pitch_mix_mlb_24.csv')
    pmix_mlb_24['Season'] = '2024'
    pmix_mlb_25 = pd.read_csv(f'{file_path}/pitch_mix_mlb_25.csv')
    pmix_mlb_25['Season'] = '2025'
    pmix_mlb = pd.concat([pmix_mlb_24,pmix_mlb_25])

except:
    pmix_mlb_24 = pd.read_csv(f'{file_path}/pitch_mix_mlb_24.csv')
    pmix_mlb_24['Season'] = '2024'
    pmix_mlb = pmix_mlb_24.copy()

pmix_milb_24 = pd.read_csv(f'{file_path}/pitch_mix_milb_24.csv')
pmix_milb_24['Season'] = '2024'

pmix_milb_25 = pd.read_csv(f'{file_path}/pitch_mix_milb_25.csv')
pmix_milb_25['Season'] = '2025'

pmix_milb = pd.concat([pmix_milb_24,pmix_milb_25])

# CSS BLOCK
st.markdown("""
    <style>
    /* Reduce padding at the top of the main content area */
    .main .block-container {
        padding-top: 0px !important;  /* Remove top padding */
    }

    /* Optional: Adjust the overall app padding */
    .css-1d391kg {
        padding-top: 0px !important;  /* Targets the main app container */
    }

    /* Existing styles */
    .stDataFrame table {
        width: 100%;
    }
    .stDataFrame td {
        text-align: center !important;
    }

    .main {
        background-color: #f8f9fa;
        padding: 20px;
        font-family: 'Roboto', sans-serif;
    }
    .player-card {
        background-color: black;
        padding: 1px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin: 0px 0;
        border: 1px solid #e9ecef;
    }
    .title {
        color: #2c3e50;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .stat-box {
        background-color: #f1f3f5;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    [data-testid="stSidebar"] {
        background-color: #9fa5a6;
        color: #e80927;
    }
    .stDataFrame {
        width: 100% !important;
    }
    @media (max-width: 768px) {
        .player-card {
            padding: 15px;
        }
        .title {
            font-size: 1.8rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_player_data():
    return pd.read_csv('https://docs.google.com/spreadsheets/d/1JgczhD5VDQ1EiXqVG-blttZcVwbZd5_Ne_mefUGwJnk/export?format=csv&gid=0')
playerinfo = load_player_data()

@st.cache_data
def get_mlb_player_info(player_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        player_data = response.json()['people'][0]
        return {
            'fullName': player_data['fullName'],
            'position': player_data['primaryPosition']['name'],
            'height': player_data['height'],
            'weight': player_data['weight'],
            'age': player_data['currentAge'],
            'bats': player_data['batSide']['description'],
            'throws': player_data['pitchHand']['description'],
            'number': player_data.get('primaryNumber', 'N/A'),
            'debut': player_data.get('mlbDebutDate', 'Not yet debuted')
        }
    except Exception as e:
        return None

def get_player_id(name_submission):
    # check if they entered a number
    check_if_number = name_submission[0].isdigit()
    if check_if_number:
        id_submission = int(name_submission)
        #st.write('User entered a number, I need to write more code')
        player_rows = playerinfo[playerinfo['MLBID']==id_submission]
        return(player_rows)
        # Number entered, move forward

    else:
        # Name entered, move forward
        player_rows = playerinfo[playerinfo['PLAYERNAME'].str.contains(name_submission, case=False)]
        if len(player_rows) == 1:
            # found exactly one name, we can return it
            return(player_rows)
        elif len(player_rows) < 1:
            # found nobody, search ZIPS file
            zips_rows = ids_zip[ids_zip['Name'].str.contains(name_submission, case=False)]
            player_rows = pd.DataFrame({'PLAYERNAME': zips_rows['Name'].iloc[0], 
                                        'MLBID': zips_rows['MLBID'].iloc[0],
                                        'FANGRAPHSID': zips_rows['FGID'].iloc[0]},index=[0])

            return(player_rows)
        elif len(player_rows) > 1:
            # More than one found, generating options for the user to select
            options = player_rows[['PLAYERNAME', 'TEAM', 'POS', 'MLBID']].copy()
            options['MLBID'] = options['MLBID'].astype(str).str.replace('.0', '')
            return(options)

def get_player_image(player_id):
    return f'https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_426,q_auto:best/v1/people/{player_id}/headshot/67/current'

def scrapeFG_pitchers(fgid):
    fgurl = f'https://www.fangraphs.com/api/players/stats?playerid={fgid}&position=P'
    response = requests.get(fgurl)
    if response.status_code == 200:
        data = response.json()

    pdata = data.get('data')
    build_df = pd.DataFrame()
    for x in pdata:
        teamshort = x.get('AbbName')
        level = x.get('AbbLevel')
        sorttype = x.get('sortType')
        season = x.get('sortSeason')
        if teamshort is None or level == 'PROJ' or sorttype == 900 or season > 3000:
            continue
        
        seasonage = x.get('Age')
        g = x.get('G')
        gs = x.get('GS')
        ip = x.get('IP')
        w = x.get('W')
        tbf = x.get('TBF')
        so = x.get('SO')
        bb = x.get('BB')

        era = x.get('ERA')
        whip = x.get('WHIP')

        krate = so / tbf
        bbrate = bb / tbf
        kbbrate = krate - bbrate

        krate = f"{krate:.3f}"
        bbrate = f"{bbrate:.3f}"
        kbbrate = f"{kbbrate:.3f}"

        siera = x.get('SIERA')
        siera = 0 if siera is None else round(siera, 2)
        xfip = x.get('xFIP')
        xfip = 0 if xfip is None else round(xfip, 2)
        vfa = x.get('pivFA')
        vfa = 0 if vfa is None else round(vfa, 2)
        stuffplus = x.get('sp_stuff')
        stuffplus = 0 if stuffplus is None else round(stuffplus, 1)
        
        brlrate = x.get('Barrel%')
        hardhit = x.get('HardHit%')
        xera = x.get('xERA')
        zonerate = x.get('pfxZone%')
        war = x.get('WAR')
        lob = x.get('LOB%')
        avg = x.get('AVG')
        swstr = x.get('SwStr%')
        #pitches = x.get('Pitches')
        #strikes = x.get('Strikes')
        #strikerate = round(float(strikes)/float(pitches),3)

        these_df = pd.DataFrame({
            'Season': str(season), 'Team': teamshort, 'Level': level, 'Age': seasonage, 'G': g, 'GS': gs, 'IP': ip, 
            'W': w, 'K%': krate, 'BB%': bbrate, 'K-BB%': kbbrate, 'SIERA': siera, 'xFIP': xfip, 'vFA': vfa, 'Stuff+': stuffplus,
            'ERA': era, 'WHIP': whip, 'SO': so, 'BB': bb, 'Brl%': brlrate, 'Hard%': hardhit, 'xERA': xera, 
            'Zone%': zonerate, 'WAR': war, 'LOB%': lob, 'AVG': avg, 'SwStr%': swstr
        }, index=[0])
        build_df = pd.concat([build_df, these_df])
    return build_df

def scrapeFG_hitters(fgid):
    fgurl = f'https://www.fangraphs.com/api/players/stats?playerid={fgid}&position=OF'
    response = requests.get(fgurl)
    if response.status_code == 200:
        data = response.json()

    pdata = data.get('data')
    build_df = pd.DataFrame()
    for x in pdata:
        teamshort = x.get('AbbName')
        level = x.get('AbbLevel')
        sorttype = x.get('sortType')
        season = x.get('sortSeason')
        if teamshort is None or level == 'PROJ' or sorttype == 900 or season > 3000:
            continue
        
        seasonage = x.get('Age')
        wrc = round(x.get('wRC+'), 0)
        g = x.get('G')
        ab = x.get('AB')
        pa = x.get('PA')
        singles = x.get('1B')
        doubles = x.get('2B')
        triples = x.get('3B')
        homers = x.get('HR')
        strikeouts = x.get('SO')
        sb = x.get('SB')
        walks = x.get('BB')
        hbp = x.get('HBP')
        sh = x.get('SH')
        sf = x.get('SF')
        pullrate = x.get('Pull%')

        krate = f"{round(strikeouts / pa, 3):.3f}"
        bbrate = f"{round(walks / pa, 3):.3f}"
        swstr = x.get('SwStr%')
        swingrate = x.get('pfxSwing%')
        zoneswing = x.get('Z-Swing%')
        oswing = x.get('O-Swing%')
        contactrate = x.get('pfxContact%')
        hits = singles + doubles + triples + homers
        r = x.get('R')
        rbi = x.get('RBI')

        avg = round(hits / ab, 3)
        obp = round((hits + walks + hbp) / pa, 3)
        slg = round(((singles) + (doubles * 2) + (triples * 3) + (homers * 4)) / ab, 3)
        ops = obp + slg
        swingrate = f"{swingrate:.3f}" if swingrate else '--'
        contactrate = f"{contactrate:.3f}" if contactrate else '--'
        swstr = f"{swstr:.3f}" if swstr else '--'


        bbe = x.get('Events')
        barrels = x.get('Barrels')
        brlrate = x.get('Barrel%')
        maxev = x.get('maxEV')
        hardhit = x.get('HardHit%')
        contactrate = x.get('Contact%')

        xavg = x.get('xAVG')
        xslg = x.get('xSLG')
        xwoba = x.get('xwOBA')
        ev = x.get('EV')
        la = x.get('LA')

        hrfb = x.get('HR/FB')
        gbrate = x.get('GB%')
        fbrate = x.get('FB%')
        ldrate = x.get('LD%')

        babip = x.get('BABIP')

        these_df = pd.DataFrame({
            'Season': str(season), 'Team': teamshort, 'Level': level, 'Age': seasonage, 'G': g, 'AB': ab, 
            'AVG': avg, 'OBP': obp, 'SLG': slg, 'OPS': ops, 'HR': homers, 'R': r, 'RBI': rbi, 'SB': sb,
            'K%': krate, 'BB%': bbrate, 'SwStr%': swstr, 'Cont%': contactrate, 'Swing%': swingrate, 'wRC+': wrc,
            'Brls': barrels, 'Brl%': brlrate, 'MaxEV': maxev, 'Hard%': hardhit, 'xBA': xavg, 'xSLG': xslg,
            'xwOBA': xwoba, 'BBE': bbe, 'EV': ev, 'LA': la,  'HR/FB': hrfb, 'GB%': gbrate,
            'LD%': ldrate, 'FB%': fbrate, 'BABIP': babip, 'Pull%': pullrate, 'ZoneSwing%': zoneswing, 'Chase%': oswing,
        }, index=[0])
        build_df = pd.concat([build_df, these_df])
    return build_df

def create_gauge_chart(stat_name, player_value, league_avg):
    """
    Create a gauge chart comparing player's stat to league average
    
    Parameters:
    stat_name (str): Name of the statistic
    player_value (float): Player's value for the stat
    league_avg (float): League average for the stat
    """
    
    # Calculate the gauge range (make it symmetric around league average)
    max_range = max(player_value, league_avg) * 1.5  # 50% buffer beyond max value
    min_range = min(player_value, league_avg) * 0.5   # 50% buffer below min value
    
    # Create gauge chart
    player_value = round(player_value,3)
    league_avg = round(league_avg,3)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=player_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': stat_name, 'font': {'size': 20}},
        gauge={
            'axis': {
                'range': [min_range, max_range],
                'tickwidth': 1,
                'tickcolor': "darkblue"
            },
            'bar': {'color': "#1f77b4"},  # Blue needle
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [min_range, league_avg * 0.9], 'color': '#ff9999'},  # Red below avg
                {'range': [league_avg * 0.9, league_avg * 1.1], 'color': '#ffff99'},  # Yellow near avg
                {'range': [league_avg * 1.1, max_range], 'color': '#99ff99'}  # Green above avg
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': .75,
                'value': league_avg
            }
        }
    ))

    # Update layout
    fig.update_layout(
        height=250,
        width=250,
        font={'size': 15}
    )

    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=False)

def main():
    with st.sidebar:
        st.markdown("<h2 style='color: black; font-weight: 700;'>MLB Player Lookup</h2>", unsafe_allow_html=True)
        name_input = st.text_input("Search Player", placeholder="Enter player name", 
                                 help="Enter a player name")
        st.markdown("<p style='color: #575654;'><b>Search for any MLB player to see detailed stats</b></p>", 
                   unsafe_allow_html=True)


    st.markdown("<h1 class='title'>MLB Data Warehouse Player Lookup</h1>", unsafe_allow_html=True)
    if name_input:
        with st.spinner("Loading player data..."):
            result = get_player_id(name_input)
            # If no players were found
            if result is None:
                st.write('No players were find, please search again.')
            # If multiple results, have them select an option
            elif len(result)>1:
                player_options = [
                    f"{row['PLAYERNAME']} ({row['TEAM']}, {row['POS']}) - MLBID: {row['MLBID']}"
                    for _, row in result.iterrows()
                ]
                selected_option = st.selectbox("Found multiple results, please select who you're looking for:", player_options)
                selected_mlbid = selected_option.split("MLBID: ")[-1]
                st.write(f'Enter {selected_mlbid} in the search to hide this box')
                result = get_player_id(selected_mlbid)
            else:
                pass
                
            #st.dataframe(result)

            # Get Player IDs
            mlbid = result['MLBID'].iloc[0]
            mlbid = int(mlbid)
            try:
                fgid = result['IDFANGRAPHS'].iloc[0]
            except:
                fgid = result['FANGRAPHSID'].iloc[0]
            # Get Player Data from MLB API
            player_data = get_mlb_player_info(mlbid)
            playerName = player_data['fullName']

            player_mlb_position = player_data['position']
            #st.write(player_mlb_position)
            if player_mlb_position == 'Pitcher':
                player_position = 'Pitcher'
                print_position = 'P'
            else:
                player_position = 'Hitter'
                posdict = {'Outfield': 'OF', 'Outfielder': 'OF', 'Second Base': '2B','Third Base': '3B', 'Shortstop': 'SS', 'Catcher': 'C', 'First Base': '1B'}
                print_position = posdict.get(player_mlb_position)
            
            #st.write(f'Working with a {player_position}, more specifically a {print_position}')
            if player_data:
                with st.container():
                    st.markdown("<div class='player-card'>", unsafe_allow_html=True)
                    col1, col2 = st.columns([1, 5], gap="small")
                    with col1:
                        #st.markdown(f'<h4>{playerName} ({print_position})', unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)

                        st.image(get_player_image(mlbid), width=185)#, caption=player_data['fullName'])
                        st.markdown(f"""<center><div style='line-height: 1.6; color: #2c3e50;'> <font size='1' face='Helvetica'><i>
                                <b>{player_data['height']} | 
                                {player_data['weight']}lbs | Bats {player_data['bats'][0:1]} | Throws {player_data['throws'][0:1]} </b></center></font>
                            </div>
                        """, unsafe_allow_html=True)
                        

                    with col2:
                        #st.subheader(player_data['fullName'] + f' ({print_position})', anchor=False)
                        st.markdown(f'<h4>{playerName} ({print_position})', unsafe_allow_html=True)

                        if player_position == 'Hitter':
                            fg_stats = scrapeFG_hitters(fgid)
                            fg_stats['K%'] = pd.to_numeric(fg_stats['K%'])
                            fg_stats['BB%'] = pd.to_numeric(fg_stats['BB%'])
                            # Determine the level
                            stat_recent = fg_stats[fg_stats['Season'].isin(['2023','2024','2025'])]
                            stat_recent['Season'] = stat_recent['Season'].astype(int)
                            most_recent = stat_recent[stat_recent['Season']==np.max(stat_recent['Season'])]

                            level_assign = most_recent.sort_values(by='AB',ascending=False)['Level'].iloc[0]
                            if level_assign == 'MLB':
                                player_level = 'MLB'
                                ## GENERATE DATA FOR MLB PLAYERS
                                tab1, tab2, tab3, tab4, tab5 = st.tabs(['Standard Data','Advanced','Statcast','Player History', 'Game Log'])
                                with tab1:
                                    showcols = ['Season','Team','G','AB','R','HR','RBI','SB','AVG','SLG','OPS','K%','BB%','wRC+']
                                    df_to_print = fg_stats[fg_stats['Season'].isin(['2025','2024','2023'])][showcols]
                                    df_to_print = df_to_print.sort_values(by='Season',ascending=False)
                                    styled_df = df_to_print.style.format({'AVG': '{:.3f}','OBP': '{:.3f}','SLG': '{:.3f}',
                                                                          'OPS': '{:.3f}','K%': '{:.3f}','BB%': '{:.3f}',
                                                                          'wRC+': '{:.0f}'})

                                    st.dataframe(styled_df,hide_index=True, width=725)
                                with tab2:
                                    showcols = ['Season','Level','Team','G','AB','Swing%','Chase%','SwStr%','GB%','FB%','BABIP','Pull%']
                                    df_to_print = fg_stats[fg_stats['Season'].isin(['2025','2024','2023'])][showcols]
                                    df_to_print = df_to_print[df_to_print['Level']=='MLB']
                                    df_to_print = df_to_print.sort_values(by='Season',ascending=False)
                                    styled_df = df_to_print.style.format({'Swing%': '{:.3f}','Chase%': '{:.3f}','SwStr%': '{:.3f}',
                                                                          'GB%': '{:.3f}', 'FB%': '{:.3f}', 'BABIP': '{:.3f}',
                                                                          'Pull%': '{:.3f}'})

                                    st.dataframe(df_to_print,hide_index=True, width=825)

                                
                                with tab3:
                                    showcols = ['Season','Level','Team','G','AB','BBE','xBA','xSLG','xwOBA','Brl%','Hard%','EV','LA','MaxEV']
                                    df_to_print = fg_stats[fg_stats['Season'].isin(['2025','2024','2023'])][showcols]
                                    df_to_print = df_to_print[df_to_print['Level']=='MLB']
                                    df_to_print = df_to_print.sort_values(by='Season',ascending=False)
                                    styled_df = df_to_print.style.format({'xBA': '{:.3f}','xSLG': '{:.3f}','xwOBA': '{:.3f}','Brl%': '{:.3f}',
                                                                          'Hard%': '{:.3f}','EV': '{:.1f}','LA': '{:.1f}','MaxEV': '{:.1f}'})

                                    st.dataframe(styled_df,hide_index=True, width=745)

                                with tab4:
                                    showcols = ['Season','Team','Level','G','AB','R','HR','RBI','SB','AVG','SLG','OPS','K%','BB%','wRC+']
                                    df_to_print = fg_stats[showcols]
                                    df_to_print = df_to_print.sort_values(by='Season',ascending=False)
                                    styled_df = df_to_print.style.format({'AVG': '{:.3f}','OBP': '{:.3f}','SLG': '{:.3f}',
                                                                          'OPS': '{:.3f}','K%': '{:.3f}','BB%': '{:.3f}',
                                                                          'wRC+': '{:.0f}'})

                                    st.dataframe(styled_df,hide_index=True, width=775, height=280)
                                with tab5:
                                    plog = hitlogs[hitlogs['player_id']==mlbid][['game_date','level','team_abbrev','opp_abbrev','AB','H','R','HR','RBI','SB','2B','3B','SO','BB','CS','DKPts']]
                                    plog = plog.rename({'team_abbrev': 'Team','opp_abbrev': 'Opp'}, axis=1)
                                    st.dataframe(plog, hide_index=True, width=1000)

                            else:
                                player_level = 'MiLB'
                                # Data
                                psav = milbsav[milbsav['batter']==mlbid]
                                ## GENERATE DATA FOR MLB PLAYERS
                                tab1, tab2, tab3 = st.tabs(['Standard Data','Advanced','Player History'])
                                
                                with tab1:
                                    showcols = ['Season','Team','Level','G','AB','R','HR','RBI','SB','AVG','SLG','OPS','K%','BB%','wRC+']
                                    df_to_print = fg_stats[fg_stats['Season'].isin(['2025','2024','2023','2022'])][showcols]
                                    df_to_print = df_to_print.sort_values(by='Season',ascending=False)
                                    df_to_print1 = df_to_print[df_to_print['Level'].isin(['MiLB','MLB'])]
                                    styled_df = df_to_print.style.format({'AVG': '{:.3f}','OBP': '{:.3f}','SLG': '{:.3f}',
                                                                          'OPS': '{:.3f}','K%': '{:.3f}','BB%': '{:.3f}',
                                                                          'wRC+': '{:.0f}'})
                                    styled_df1 = df_to_print1.style.format({'AVG': '{:.3f}','OBP': '{:.3f}','SLG': '{:.3f}',
                                                                          'OPS': '{:.3f}','K%': '{:.3f}','BB%': '{:.3f}',
                                                                          'wRC+': '{:.0f}'})


                                    st.dataframe(styled_df1,hide_index=True, width=770)
                                with tab2:
                                    
                                    show_fg = fg_stats[['Season','Team','Level','G','AB','wRC+','GB%','LD%','FB%','BABIP','Pull%']]
                                    show_fg = show_fg[show_fg['Level'].isin(['MLB','MiLB'])]
                                    
                                    show_sav = psav[psav['Split']=='All'][['Year','Cont%','Swing%','Statcast BBE','EV 90']]
                                    show_sav.columns=['Season','Cont%','Swing%','BBE','EV 90']
                                    
                                    df_to_print = pd.merge(show_fg, show_sav, on='Season',how='outer')
                                    df_to_print = df_to_print[df_to_print['Season']!='2025']
                                    styled_df = df_to_print.style.format({'GB%': '{:.3f}','wRC+': '{:.0f}','LD%': '{:.3f}','FB%': '{:.3f}',
                                                                          'BABIP': '{:.3f}','Pull%': '{:.3f}','Cont%': '{:.3f}','Swing%': '{:.3f}',
                                                                          'G': '{:.0f}','AB': '{:.0f}','BBE': '{:.0f}','EV 90': '{:.1f}'})

                                    st.dataframe(styled_df, hide_index=True, width=825)

                                
                                with tab3:
                                    showcols = ['Season','Team','Level','G','AB','R','HR','RBI','SB','AVG','SLG','OPS','K%','BB%','wRC+']
                                    df_to_print = fg_stats[showcols]
                                    df_to_print = df_to_print.sort_values(by='Season',ascending=False)
                                    styled_df = df_to_print.style.format({'AVG': '{:.3f}','OBP': '{:.3f}','SLG': '{:.3f}',
                                                                          'OPS': '{:.3f}','K%': '{:.3f}','BB%': '{:.3f}',
                                                                          'wRC+': '{:.0f}'})

                                    st.dataframe(styled_df,hide_index=True, width=855, height=300)
                            
                            

                        elif player_position == 'Pitcher':
                            fg_stats = scrapeFG_pitchers(fgid)
                            fg_stats['K%'] = pd.to_numeric(fg_stats['K%'])
                            fg_stats['BB%'] = pd.to_numeric(fg_stats['BB%'])
                            fg_stats['K-BB%'] = fg_stats['K%']-fg_stats['BB%']
                            fg_stats['G'] = pd.to_numeric(fg_stats['G'])
                            fg_stats['GS'] = pd.to_numeric(fg_stats['GS'])
                            fg_stats['IP'] = pd.to_numeric(fg_stats['IP'])
                            fg_stats['SO'] = pd.to_numeric(fg_stats['SO'])
                            fg_stats['BB'] = pd.to_numeric(fg_stats['BB'])
                            fg_stats['W'] = pd.to_numeric(fg_stats['W'])
                            fg_stats['ERA'] = pd.to_numeric(fg_stats['ERA'])
                            fg_stats['WHIP'] = pd.to_numeric(fg_stats['WHIP'])
                            fg_stats['SIERA'] = pd.to_numeric(fg_stats['SIERA'], errors='ignore')
                            #fg_stats['SIERA'] = fg_stats['SIERA'].str[0:]

                            stat_recent = fg_stats[fg_stats['Season'].isin(['2023','2024','2025'])]
                            stat_recent['Season'] = stat_recent['Season'].astype(int)
                            most_recent = stat_recent[stat_recent['Season']==np.max(stat_recent['Season'])]

                            level_assign = most_recent.sort_values(by='IP',ascending=False)['Level'].iloc[0]                            

                            tab1, tab2, tab3, tab4, tab5 = st.tabs(['Standard Data','Advanced','Pitch Mix','Player History', 'Game Log'])

                            with tab1:
                                show_cols = ['Season','Team','Level','G','GS','IP','SO','BB','W','ERA','WHIP','K%','BB%','K-BB%','SIERA']
                                df_to_print = fg_stats[show_cols]
                                df_to_print = df_to_print[df_to_print['Level'].isin(['MiLB','MLB'])]
                                df_to_print = df_to_print[df_to_print['Season'].isin(['2025','2024','2023'])]
                                df_to_print = df_to_print.sort_values(by='Season',ascending=False)
                                styled_df = df_to_print.style.format({'G': '{:.0f}',
                                                                      'GS': '{:.0f}',
                                                                      'IP': '{:.0f}',
                                                                      'SO': '{:.0f}',
                                                                      'BB': '{:.0f}',
                                                                      'W': '{:.0f}',
                                                                      'ERA': '{:.2f}',
                                                                      'WHIP': '{:.2f}',
                                                                      'K%': '{:.3f}',
                                                                      'BB%': '{:.3f}',
                                                                      'K-BB%': '{:.3f}',
                                                                      'SIERA': '{:.2f}'})
                                st.dataframe(styled_df,hide_index=True, width=790)
                            
                            with tab2:
                                show_cols = ['Season','Team','Level','G','GS','IP','K%','BB%','SwStr%','SIERA','xFIP','xERA','Zone%','LOB%']
                                df_to_print = fg_stats[show_cols]
                                df_to_print = df_to_print[df_to_print['Level'].isin(['MiLB','MLB'])]
                                df_to_print = df_to_print[df_to_print['Season'].isin(['2025','2024','2023'])]
                                df_to_print = df_to_print.sort_values(by='Season',ascending=False)
                                styled_df = df_to_print.style.format({'G': '{:.0f}',
                                                                      'GS': '{:.0f}',
                                                                      'IP': '{:.0f}',
                                                                      'SIERA': '{:.2f}',
                                                                      'xFIP': '{:.2f}',
                                                                      'xERA': '{:.2f}',
                                                                      'K%': '{:.3f}',
                                                                      'BB%': '{:.3f}',
                                                                      'SwStr%': '{:.3f}',
                                                                      'Zone%': '{:.3f}',
                                                                      'LOB%': '{:.3f}', })
                                try:
                                    st.dataframe(styled_df,hide_index=True, width=790)
                                except:
                                    st.dataframe(df_to_print,hide_index=True, width=790)
                            
                            with tab3:
                                if level_assign == 'MLB':
                                    pmix = pmix_mlb[pmix_mlb['pitcher']==mlbid]
                                else:
                                    pmix = pmix_milb[pmix_milb['pitcher']==mlbid]
                                
                                show_df = pmix[['Season','pitch_type','PC','Velo','SwStr%','Strike%','Ball%','GB%']]
                                
                                show_df = show_df[show_df['Season']==np.max(show_df['Season'])]
                                #show_df['PC'] = pd.to_numeric(show_df['PC'])
                                show_df = show_df.sort_values(by='PC',ascending=False)
                                styled_df = show_df.style.format({'PC': '{:.0f}', 'Velo': '{:.1f}', 'SwStr%': '{:.3f}', 'Strike%': '{:.3f}', 'Ball%': '{:.3f}', 'GB%': '{:.3f}'})
                                st.dataframe(styled_df,hide_index=True,width=490)


                            with tab4:
                                show_cols = ['Season','Team','Level','G','GS','IP','SO','BB','W','ERA','WHIP','K%','BB%','K-BB%','SIERA']
                                df_to_print = fg_stats[show_cols]
                                df_to_print = df_to_print.sort_values(by='Season',ascending=False)
                                styled_df = df_to_print.style.format({'G': '{:.0f}',
                                                                      'GS': '{:.0f}',
                                                                      'IP': '{:.0f}',
                                                                      'SO': '{:.0f}',
                                                                      'BB': '{:.0f}',
                                                                      'W': '{:.0f}',
                                                                      'ERA': '{:.2f}',
                                                                      'WHIP': '{:.2f}',
                                                                      'K%': '{:.3f}',
                                                                      'BB%': '{:.3f}',
                                                                      'K-BB%': '{:.3f}',
                                                                      'SIERA': '{:.2f}'})
                                st.dataframe(styled_df,hide_index=True, width=800, height=350)
                            
                            with tab5:
                                p_log = pitchlogs[pitchlogs['player_id']==mlbid]
                                p_log = p_log[['game_date','level','team_abbrev','opp_abbrev','G','GS','IP','H','ER','SO','BB','HR','DKPts']]
                                p_log = p_log.rename({'game_date': 'Date', 'team_abbrev': 'Team','opp_abbrev': 'Opp'},axis=1)
                                styled_df = p_log.style.format({'G': '{:.0f}','GS': '{:.0f}','IP': '{:.1f}','H': '{:.0f}','SO': '{:.0f}',
                                                                'BB': '{:.0f}','HR': '{:.0f}','DKPts': '{:.1f}'})

                                st.dataframe(styled_df,hide_index=True, width=800, height=200)



                        else:
                            st.write('No position found')

                if player_position == 'Hitter':

                    st.markdown("<center><h4>JA Model Skills Data</h4></center>", unsafe_allow_html=True)
                    #st.markdown("<center><i>black line on gauge represents league average</center>", unsafe_allow_html=True)
                    pskills = hskills[hskills['SAVID']==mlbid][['K%','BB%','Brl%','SBAtt%','SBSuccess%']]
                    if len(pskills)!=1:
                        have_skills = 'N'
                    else:
                        have_skills = 'Y'
                    
                    p_fscores = fscores_h[fscores_h['Name']==playerName]
                    
                    if len(p_fscores)!=1:
                        have_fscore = 'N'
                    else:
                        have_fscore = 'Y'
                        p_fcont = p_fscores['fContact'].iloc[0]
                        p_fdisc = p_fscores['fDiscipline'].iloc[0]
                        p_fpower = p_fscores['fPower'].iloc[0]
                        p_fspeed = p_fscores['fSpeed'].iloc[0]
                        
                    if have_skills == 'Y':
                        col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="small")
                        with col1:
                            player_k = pskills['K%'].iloc[0]
                            league_k = .225
                            stat_name = 'K%'
                            create_gauge_chart(stat_name, player_k, league_k)
                        with col2:
                            player_bb = pskills['BB%'].iloc[0]
                            league_bb = .079
                            stat_name = 'BB%'
                            create_gauge_chart(stat_name, player_bb, league_bb)
                        with col3:
                            player_brl = pskills['Brl%'].iloc[0]
                            league_brl = .078
                            stat_name = 'Brl%'
                            create_gauge_chart(stat_name, player_brl, league_brl)
                        with col4:
                            player_sb = pskills['SBAtt%'].iloc[0]
                            league_sb = .107
                            stat_name = 'SBAtt%'
                            create_gauge_chart(stat_name, player_sb, league_sb)
                    
                    if have_fscore == 'Y':
                        st.markdown("<center><h4>Tim Kanak fScores</h4></center>", unsafe_allow_html=True)
                        col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="small")
                        with col1:
                            create_gauge_chart('fContact', p_fcont, 100)
                        with col2:
                            create_gauge_chart('fDiscipline', p_fdisc, 100)
                        with col3:
                            create_gauge_chart('fPower', p_fpower, 100)
                        with col4:
                            create_gauge_chart('fSpeed', p_fspeed, 100)

                ###
                else:
                    st.markdown("<center><h4>JA Model Skills Projection & Tim Kanak fScores</h4></center>", unsafe_allow_html=True)
                    #st.markdown("<center><i>black line on gauge represents league average</center>", unsafe_allow_html=True)
                    pskills = pitchskills[pitchskills['SAVID']==mlbid][['K%','BB%']]
                    if len(pskills)!=1:
                        have_skills = 'N'
                    else:
                        have_skills = 'Y'
                    
                    p_fscores = fscores_pitch[fscores_pitch['Name']==playerName]
                    
                    if len(p_fscores)!=1:
                        have_fscore = 'N'
                    else:
                        have_fscore = 'Y'
                        p_fdur = p_fscores['fPDurability'].iloc[0]
                        fStuff = p_fscores['fStuff'].iloc[0]
                        fControl = p_fscores['fControl'].iloc[0]
                        fERA = p_fscores['fERA'].iloc[0]
                        
                    if have_skills == 'Y':
                        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1], gap="small")
                        with col1:
                            player_k = pskills['K%'].iloc[0]
                            league_k = .225
                            stat_name = 'K%'
                            create_gauge_chart(stat_name, player_k, league_k)
                        with col2:
                            player_bb = pskills['BB%'].iloc[0]
                            league_bb = .079
                            stat_name = 'BB%'
                            create_gauge_chart(stat_name, player_bb, league_bb)
                        
                        with col3:
                            create_gauge_chart('fContact', p_fdur, 100)
                        with col4:
                            create_gauge_chart('fStuff', fStuff, 100)
                        with col5:
                            create_gauge_chart('fControl', fControl, 100)
                        with col6:
                            create_gauge_chart('fERA', fERA, 100)    

            
            

if __name__ == "__main__":
    main()