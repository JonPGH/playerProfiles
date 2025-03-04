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

base_dir = os.path.dirname(__file__)
file_path = os.path.join(base_dir, 'Data')

# Data Load
minorsdata24 = pd.read_csv(f'{file_path}/hit_minors_advanced24.csv')
minorsdata25 = pd.read_csv(f'{file_path}/hit_minors_advanced25.csv')
majorsdata24 = pd.read_csv(f'{file_path}/hit_majors_advanced24.csv')
majorsdata25 = pd.read_csv(f'{file_path}/hit_majors_advanced25.csv')
hprojections = pd.read_csv(f'{file_path}/ja_h.csv')
pprojections = pd.read_csv(f'{file_path}/ja_p.csv')
fscores_h = pd.read_csv(f'{file_path}/fScoresHit.csv')
hitlogs = pd.read_csv(f'{file_path}/hitdb25.csv').sort_values(by='game_date', ascending=False)
ids_zip = pd.read_csv(f'{file_path}/zips_ids.csv')
ids_zip['MLBID'] = ids_zip['MLBID'].astype(str)
ids_zip['FGID'] = ids_zip['FGID'].astype(str)

# Custom CSS for modern styling
st.markdown("""
    <style>
            
    /* Target all dataframe tables */
    .stDataFrame table {
        width: 100%;  /* Optional: adjust width if needed */
    }
    .stDataFrame td {
        text-align: center !important;  /* Center-align all table cells */
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
    .sidebar .sidebar-content {
        background-color: #2c3e50;
        color: white;
        padding: 20px;
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

def getProjection(check_pos, playername):
    if check_pos == 'Hitter':
        this_proj = hprojections[hprojections['Player'].str.contains(playername)]
        this_proj = this_proj[['Player','Team','PA','R','HR','RBI','SB','AVG','OBP','SLG','OPS']]
    else:
        this_proj = pprojections[pprojections['Pitcher'].str.contains(playername)]
        this_proj = this_proj[['Pitcher','Team','GS','IP','ERA','WHIP','K%','BB%','GB%']]

    return(this_proj)


def getGameLogs(mlbid):
    plog = hitlogs[hitlogs['player_id'] == mlbid]
    plog = plog[['Player', 'game_date', 'game_type', 'level', 'team_abbrev', 'opp_abbrev', 'AB', 'H', 'R', 'HR', 'RBI', '2B', '3B', 'SB', 'DKPts']].head(15)
    plog.columns = ['Player', 'Date', 'Type', 'Level', 'Team', 'Opp', 'AB', 'H', 'R', 'HR', 'RBI', '2B', '3B', 'SB', 'DKPts']
    return plog

def loadFScores(player_name):
    player_fscore = fscores_h[fscores_h['Name'] == player_name]
    return player_fscore

def loadAdvData(mlbid):
    psav24 = minorsdata24[minorsdata24['batter'] == mlbid]
    psav24['Year'] = '2024'
    psav25 = minorsdata25[minorsdata25['batter'] == mlbid]
    psav25['Year'] = '2025'
    psav = pd.concat([psav24, psav25])
    psav_minors = psav.copy()
    psav_minors['Level'] = 'Minors'

    psav24 = majorsdata24[majorsdata24['batter'] == mlbid]
    psav24['Year'] = '2024'
    psav25 = majorsdata25[majorsdata25['batter'] == mlbid]
    psav25['Year'] = '2025'
    psav = pd.concat([psav24, psav25])
    psav_majors = psav.copy()
    psav_majors['Level'] = 'MLB'

    psav = pd.concat([psav_minors, psav_majors])
    return psav

def create_stat_gauges(fContact, fPower, fSpeed, fDiscipline):
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
               [{'type': 'indicator'}, {'type': 'indicator'}]],
        vertical_spacing=0
    )

    gauge_config = {
        'axis': {'range': [0, 200], 'tickwidth': 1, 'tickcolor': "darkblue", 'nticks': 5, 'showticklabels': True},
        'bar': {'color': "#FFFFFF", 'thickness': 0.2},
        'bgcolor': "blue",
        'borderwidth': 2,
        'bordercolor': "red",
        'steps': [
            {'range': [0, 50], 'color': 'black'},
            {'range': [50, 100], 'color': 'black'},
            {'range': [100, 150], 'color': 'black'},
            {'range': [150, 200], 'color': 'black'}
        ],
        'threshold': {'line': {'color': "blue", 'width': 4}, 'thickness': 0.75, 'value': 100}
    }

    fig.add_trace(go.Indicator(mode="gauge+number", value=fContact, title={'text': "Contact", 'font': {'size': 16}}, 
                              gauge=gauge_config, number={'font': {'size': 30}}), row=1, col=1)
    fig.add_trace(go.Indicator(mode="gauge+number", value=fPower, title={'text': "Power", 'font': {'size': 16}}, 
                              gauge=gauge_config, number={'font': {'size': 30}}), row=1, col=2)
    fig.add_trace(go.Indicator(mode="gauge+number", value=fSpeed, title={'text': "Speed", 'font': {'size': 16}}, 
                              gauge=gauge_config, number={'font': {'size': 30}}), row=2, col=1)
    fig.add_trace(go.Indicator(mode="gauge+number", value=fDiscipline, title={'text': "Discipline", 'font': {'size': 16}}, 
                              gauge=gauge_config, number={'font': {'size': 30}}), row=2, col=2)

    fig.update_layout(
        height=400, width=400, margin=dict(t=50, b=50, l=50, r=50),
        title_text="Tim Kanak fScores (League Average = 100)", title_x=0.14, title_font_size=15,
        grid={'rows': 2, 'columns': 2, 'pattern': "independent"}
    )
    return fig

def get_player_id(player_name):
    try:
        if player_name[0] == '6':
            pid = int(player_name)
            player_rows = playerinfo[playerinfo['MLBID'] == pid]
        else:
            player_rows = playerinfo[playerinfo['PLAYERNAME'].str.contains(player_name, case=False)]
        
        if len(player_rows) == 0:
            player_rows = ids_zip[ids_zip['Name'].str.contains(player_name, case=False)]
            if len(player_rows) == 1:
                mlbid = int(player_rows['MLBID'].iloc[0])
                fgid = player_rows['FGID'].iloc[0]
                return {'MLBID': mlbid, 'FGID': fgid}, None
            elif len(player_rows) > 1:
                show_multiple = player_rows[['PLAYERNAME', 'TEAM', 'POS', 'MLBID']]
                show_multiple['MLBID'] = show_multiple['MLBID'].astype(str)
                show_multiple['MLBID'] = show_multiple['MLBID'].replace('.0', '')
                st.dataframe(show_multiple)
                return None, f'{len(player_rows)} players found, choose an MLBID above and search that'
        
        elif len(player_rows) > 1:
            show_multiple = player_rows[['PLAYERNAME', 'TEAM', 'POS', 'MLBID']]
            show_multiple['MLBID'] = show_multiple['MLBID'].astype(str)
            show_multiple['MLBID'] = show_multiple['MLBID'].replace('.0', '')
            st.dataframe(show_multiple)
            return None, f'{len(player_rows)} players found, choose an MLBID above and search that'
        else:
            mlbid = int(player_rows['MLBID'].iloc[0])
            fgid = player_rows['IDFANGRAPHS'].iloc[0]
            return {'MLBID': mlbid, 'FGID': fgid}, None
    except Exception as e:
        return None, f"Error finding player: {e}"

def get_player_image(player_id):
    return f'https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_426,q_auto:best/v1/people/{player_id}/headshot/67/current'

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

        krate = so / tbf
        bbrate = bb / tbf
        kbbrate = krate - bbrate

        krate = f"{krate:.3f}"
        bbrate = f"{bbrate:.3f}"
        kbbrate = f"{kbbrate:.3f}"

        siera = x.get('SIERA')
        siera = '--' if siera is None else round(siera, 2)
        xfip = x.get('xFIP')
        xfip = '--' if xfip is None else round(xfip, 2)
        vfa = x.get('pivFA')
        vfa = '--' if vfa is None else round(vfa, 2)
        stuffplus = x.get('sp_stuff')
        stuffplus = '--' if stuffplus is None else round(stuffplus, 1)

        these_df = pd.DataFrame({
            'Season': str(season), 'Team': teamshort, 'Level': level, 'Age': seasonage, 'G': g, 'GS': gs, 'IP': ip, 
            'W': w, 'K%': krate, 'BB%': bbrate, 'K-BB%': kbbrate, 'SIERA': siera, 'xFIP': xfip, 'vFA': vfa, 'Stuff+': stuffplus
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
        walks = x.get('BB')
        hbp = x.get('HBP')
        sh = x.get('SH')
        sf = x.get('SF')
        krate = f"{round(strikeouts / pa, 3):.3f}"
        bbrate = f"{round(walks / pa, 3):.3f}"
        swstr = x.get('SwStr%')
        swingrate = x.get('pfxSwing%')
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

        these_df = pd.DataFrame({
            'Season': str(season), 'Team': teamshort, 'Level': level, 'Age': seasonage, 'G': g, 'AB': ab, 
            'AVG': avg, 'OBP': obp, 'SLG': slg, 'OPS': ops, 'HR': homers, 'R': r, 'RBI': rbi,
            'K%': krate, 'BB%': bbrate, 'SwStr%': swstr, 'Cont%': contactrate, 'Swing%': swingrate, 'wRC+': wrc
        }, index=[0])
        build_df = pd.concat([build_df, these_df])
    return build_df

def main():
    with st.sidebar:
        st.markdown("<h2 style='color: black; font-weight: 700;'>MLB Player Lookup</h2>", unsafe_allow_html=True)
        name_input = st.text_input("Search Player", placeholder="Enter player name or MLBID...", 
                                 help="Enter a name or MLBID to view player stats")
        st.markdown("<p style='color: #575654;'>Search for any MLB player to see detailed stats</p>", 
                   unsafe_allow_html=True)

    st.markdown("<h1 class='title'>MLB Data Warehouse Player Lookup</h1>", unsafe_allow_html=True)

    if name_input:
        with st.spinner("Loading player data..."):
            result, error = get_player_id(name_input)

            if error:
                st.error(error)
            elif result:
                mlbid = result['MLBID']
                fgid = result['FGID']
                player_data = get_mlb_player_info(mlbid)

                pinfo_pos = player_data['position']
                if pinfo_pos == 'Pitcher':
                    check_pos = 'Pitcher'
                else:
                    check_pos = 'Hitter'
                posdict = {'Outfielder': 'OF', 'Second Base': '2B','Third Base': '3B', 'Shortstop': 'SS', 'Catcher': 'C', 'First Base': '1B'}
                showpos = posdict.get(pinfo_pos)
                if showpos is None:
                    showpos = pinfo_pos

                if player_data:
                    with st.container():
                        st.markdown("<div class='player-card'>", unsafe_allow_html=True)
                        col1, col2 = st.columns([1, 4], gap="small")
                        
                        with col1:
                            st.image(get_player_image(mlbid), width=200)#, caption=player_data['fullName'])
                            st.markdown(f"""<div style='line-height: 1.6; color: #2c3e50;'> <font size='2' face='Helvetica'><i>
                                    <b>{player_data['height']} | 
                                    {player_data['weight']}lbs | Bats {player_data['bats'][0:1]} | Throws {player_data['throws'][0:1]} </b></font>
                                </div>
                            """, unsafe_allow_html=True)

                        with col2:
                            st.subheader(player_data['fullName'] + f' ({showpos})', anchor=False)
                            tab1, tab2, tab3, tab4 = st.tabs(["Season Stats", "Splits", "Statcast", "Game Log"])
                            
                            with tab1:
                                fg_data = scrapeFG_pitchers(fgid) if check_pos == 'Pitcher' else scrapeFG_hitters(fgid)
                                mlb_g = np.sum(fg_data[fg_data['Level'] == 'MLB']['G'])
                                data24 = fg_data[(fg_data['Season'].isin(['2022', '2023', '2024', '2025'])) & 
                                               (fg_data['Level'].isin(['MLB'] if mlb_g >= 5 else ['MiLB', 'MLB']))]
                                data24 = data24.sort_values(by='Season', ascending=False)
                                st.dataframe(data24, hide_index=True, use_container_width=True)

                            with tab2:
                                adv_data = loadAdvData(mlbid)
                                
                                adv_data['ISO'] = adv_data['SLG'] - adv_data['AVG']
                                showdf = adv_data[['Year', 'Level', 'Split', 'PA_flag', 'AVG', 'OBP', 'SLG', 'ISO', 'IsHomer', 'K%', 'BB%', 'Cont%']]
                                showdf = showdf[showdf['Split'] != 'All'].rename({'PA_flag': 'PA', 'IsHomer': 'HR'}, axis=1)
                                player_level = 'Majors' if showdf.groupby('Level')['PA'].sum().get('MLB', 0) > 99 else 'Minors'
                                showdf = showdf[showdf['Level'] == ('MLB' if player_level == 'Majors' else 'Minors')]
                                

                                styled_df = showdf.style.format({'PA': '{:.0f}', 'HR': '{:.0f}', 'AVG': '{:.3f}', 'OBP': '{:.3f}', 
                                                                'SLG': '{:.3f}', 'ISO': '{:.3f}', 'K%': '{:.3f}', 'BB%': '{:.3f}', 'Cont%': '{:.3f}'})
                                st.dataframe(styled_df, hide_index=True, use_container_width=True)
                            with tab3:
                                #st.markdown("<h4>Statcast</h4>", unsafe_allow_html=True)
                                launch_profile = adv_data[['Year', 'Level', 'Statcast BBE','Brl%','xwOBA','xBA', 'GB%', 'LD%', 'FB%', 'SwtSpot%', 'EV 90']].rename({'Statcast BBE': 'BBE'}, axis=1).drop_duplicates()
                                launch_profile = launch_profile[launch_profile['Level'] == ('MLB' if player_level == 'Majors' else 'Minors')]
                                styled_df = launch_profile.style.format({'BBE': '{:.0f}', 'GB%': '{:.3f}', 'LD%': '{:.3f}', 'FB%': '{:.3f}', 
                                                                        'Brl%': '{:.3f}', 'SwtSpot%': '{:.3f}','xwOBA': '{:.3f}', 'xBA': '{:.3f}',  'EV 90': '{:.1f}'})
                                st.dataframe(styled_df, hide_index=True, use_container_width=True)

                            with tab4:
                                gamelog = getGameLogs(int(mlbid))
                                st.dataframe(gamelog, hide_index=True, use_container_width=True)
                        
                        st.divider()  # Adds a horizontal rule
                        
                        col1, col2 = st.columns([1,2])
                        
                        with col1:
                            fscores = loadFScores(player_data['fullName'])
                            fContact = fscores['fContact'].iloc[0] if len(fscores) > 0 else 0
                            fPower = fscores['fPower'].iloc[0] if len(fscores) > 0 else 0
                            fSpeed = fscores['fSpeed'].iloc[0] if len(fscores) > 0 else 0
                            fDiscipline = fscores['fDiscipline'].iloc[0] if len(fscores) > 0 else 0
                            stats_fig = create_stat_gauges(fContact, fPower, fSpeed, fDiscipline)
                            st.plotly_chart(stats_fig, use_container_width=True)
                        with col2:
                            st.markdown("<h4 style='color: black; font-weight: 700;'>2025 JA Projection</h4>", unsafe_allow_html=True)

                            if check_pos == 'Hitter':
                                playerproj = getProjection(check_pos, player_data['fullName'])
                                if len(playerproj)<1:
                                    st.write('No projection to display')
                                else:
                                    st.dataframe(playerproj,hide_index=True)
                            else:
                                playerproj = getProjection(check_pos, player_data['fullName'])
                                if len(playerproj)<1:
                                    st.write('No projection to display')
                                else:
                                    st.dataframe(playerproj,hide_index=True)

                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.error("Unable to fetch player information")
    else:
        st.info("Enter a player name or MLBID in the sidebar to get started.")

if __name__ == "__main__":
    main()