import streamlit as st, numpy as np
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

## Data Load
# minor league advanced data (updates in colab)
minorsdata24 = pd.read_csv('{}/hit_minors_advanced24.csv'.format(file_path))
minorsdata25 = pd.read_csv('{}/hit_minors_advanced25.csv'.format(file_path))

majorsdata24 = pd.read_csv('{}/hit_majors_advanced24.csv'.format(file_path))
majorsdata25 = pd.read_csv('{}/hit_majors_advanced25.csv'.format(file_path))

# skill data MAKE SURE THESE ARE UPDATED FOR 2025, THE FILE LOCATION WILL CHANGE
hit_skill_data = pd.read_csv('{}/HitterSkillData.csv'.format(file_path))

# fScores from Tim (need to hook this up so his updates are taken live)
fscores_h = pd.read_csv('{}/fScoresHit.csv'.format(file_path))

# hitdb for game logs (need to hook this into my Google Drive to get daily updates)
hitlogs = pd.read_csv('{}/hitdb25.csv'.format(file_path))
hitlogs = hitlogs.sort_values(by='game_date',ascending=False)

# ids from big ZIPS file
ids_zip = pd.read_csv('{}/zips_ids.csv'.format(file_path))
ids_zip['MLBID'] = ids_zip['MLBID'].astype(str)
ids_zip['FGID'] = ids_zip['FGID'].astype(str)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
        padding: 20px;
    }
    .player-card {
        background-color: black;
        padding: 1px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 10, 0.1);
        margin: 10px 0;
    }
    .title {
        color: #1E2749;
        font-family: 'Arial', sans-serif;
    }
    .stat-box {
        background-color: #EAF4F4;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .sidebar .sidebar-content {
        background-color: #1E2749;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Data
@st.cache_data
def load_player_data():
    return pd.read_csv('https://docs.google.com/spreadsheets/d/1JgczhD5VDQ1EiXqVG-blttZcVwbZd5_Ne_mefUGwJnk/export?format=csv&gid=0')
playerinfo = load_player_data()

def getGameLogs(mlbid):
    plog = hitlogs[hitlogs['player_id']==mlbid]
    plog = plog[['Player','game_date','game_type','level','team_abbrev','opp_abbrev','AB','H','R','HR','RBI','2B','3B','SB','DKPts']].head(15)
    plog.columns=['Player','Date','Type','Level','Team','Opp','AB','H','R','HR','RBI','2B','3B','SB','DKPts']
    return(plog)

def getSkills(mlbid):
    hskills = hit_skill_data[hit_skill_data['SAVID']==mlbid]
    hskills = hskills[['Player','SAVID','K%','BB%','Brl%','Solid%','Flare%','Under%','Topped%','Weak%','BrlHR','SBAtt%','SBSuccess%']]
    return(hskills)

def loadFScores(player_name):
    player_fscore = fscores_h[fscores_h['Name']==player_name]
    return(player_fscore)

def loadAdvData(mlbid):
    psav24 = minorsdata24[minorsdata24['batter']==mlbid]
    psav24['Year'] = '2024'
    psav25 = minorsdata25[minorsdata25['batter']==mlbid]
    psav25['Year'] = '2025'
    psav = pd.concat([psav24,psav25])
    psav_minors = psav.copy()
    psav_minors['Level'] = 'Minors'


    psav24 = majorsdata24[majorsdata24['batter']==mlbid]
    psav24['Year'] = '2024'
    psav25 = majorsdata25[majorsdata25['batter']==mlbid]
    psav25['Year'] = '2025'
    psav = pd.concat([psav24,psav25])
    psav_majors = psav.copy()
    psav_majors['Level'] = 'MLB'

    psav = pd.concat([psav_minors,psav_majors])

    return(psav)

def create_stat_gauges(fContact, fPower, fSpeed, fDiscipline):
    # Create subplot with 2 rows and 2 columns
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
               [{'type': 'indicator'}, {'type': 'indicator'}]],
        #subplot_titles=['Contact', 'Power', 'Speed', 'Discipline'],
        vertical_spacing=0  # Increase vertical spacing between rows
    )

    # Common gauge configuration
    gauge_config = {
        'axis': {
            'range': [0, 200],
            'tickwidth': 1,
            'tickcolor': "darkblue",
            'nticks': 5,
            'showticklabels': True
        },
        'bar': {'color': "#FFFFFF", 'thickness': 0.2},
        'bgcolor': "white",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, 50], 'color': '#FF6B6B'},
            {'range': [50, 100], 'color': '#FFD93D'},
            {'range': [100, 150], 'color': '#6BCB77'},
            {'range': [150, 200], 'color': '#4D96FF'}
        ],
        'threshold': {
            'line': {'color': "blue", 'width': 4},
            'thickness': 0.75,
            'value': 10
        }
    }

    # Contact gauge (Row 1, Col 1)
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=fContact,
            title={'text': "Contact", 'font': {'size': 16}},
            gauge=gauge_config,
            number={'font': {'size': 40}}
        ),
        row=1, col=1
    )

    # Power gauge (Row 1, Col 2)
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=fPower,
            title={'text': "Power", 'font': {'size': 16}},
            gauge=gauge_config,
            number={'font': {'size': 40}}
        ),
        row=1, col=2
    )

    # Speed gauge (Row 2, Col 1)
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=fSpeed,
            title={'text': "Speed", 'font': {'size': 16}},
            gauge=gauge_config,
            number={'font': {'size': 40}}
        ),
        row=2, col=1
    )

    # Discipline gauge (Row 2, Col 2)
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=fDiscipline,
            title={'text': "Discipline", 'font': {'size': 16}},
            gauge=gauge_config,
            number={'font': {'size': 40}}
        ),
        row=2, col=2
    )

    # Update layout
    fig.update_layout(
        height=500,  # Increased height to accommodate two rows
        width=500,   # Adjusted width for better proportion
        margin=dict(t=50, b=50, l=50, r=50),  # Adjusted margins
        title_text="Player fScores (League Average = 100)",
        title_x=.25,  # Center the title
        title_font_size=20,
        grid={'rows': 2, 'columns': 2, 'pattern': "independent"}
    )

    return fig

def get_player_id(player_name):
    try:
        if player_name[0] == '6':
            pid = int(player_name)
            player_rows = playerinfo[playerinfo['MLBID']==pid]
        else:
            player_rows = playerinfo[playerinfo['PLAYERNAME'].str.contains(player_name, case=False)]
        
        if len(player_rows) == 0:
            player_rows = ids_zip[ids_zip['Name'].str.contains(player_name,case=False)]
            if len(player_rows)==1:
                mlbid = int(player_rows['MLBID'].iloc[0])
                fgid = player_rows['FGID'].iloc[0]
                return {'MLBID': mlbid, 'FGID': fgid}, None
            elif len(player_rows)>1:
                show_multiple = player_rows[['PLAYERNAME','TEAM','POS','MLBID']]
                show_multiple['MLBID'] = show_multiple['MLBID'].astype(str)
                show_multiple['MLBID'] = show_multiple['MLBID'].replace('.0','')
                st.dataframe(show_multiple)
                return None, f'{len(player_rows)} players found, choose an MLBID above and search that'

                
        elif len(player_rows) > 1:
            show_multiple = player_rows[['PLAYERNAME','TEAM','POS','MLBID']]
            show_multiple['MLBID'] = show_multiple['MLBID'].astype(str)
            show_multiple['MLBID'] = show_multiple['MLBID'].replace('.0','')
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
    fgurl = 'https://www.fangraphs.com/api/players/stats?playerid={}&position=P'.format(fgid)
    response = requests.get(fgurl)

    # Check if request was successful
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

        krate = so/tbf
        bbrate = bb/tbf
        kbbrate = krate-bbrate

        krate = f"{krate:.3f}"
        bbrate = f"{bbrate:.3f}"
        kbbrate = f"{kbbrate:.3f}"

        siera = x.get('SIERA')
        if siera is None:
            siera = '--'
        else:
            siera = round(siera,2)

        xfip = x.get('xFIP')
        if xfip is None:
            xfip = '--'
        else:
            xfip = round(xfip,2)
        
        vfa = x.get('pivFA')
        if vfa is None:
            vfa = '--'
        else:
            vfa = round(vfa,2)
        
        stuffplus = x.get('sp_stuff')
        if stuffplus is None:
            stuffplus = '--'
        else:
            stuffplus = round(stuffplus,1)
        

        these_df = pd.DataFrame({'Season': str(season), 'Team': teamshort, 'Level': level,
                                'Age': seasonage, 'G': g, 'GS': gs, 'IP': ip, 'W': w, 'K%': krate, 'BB%': bbrate,
                                'K-BB%': kbbrate, 'SIERA': siera, 'xFIP': xfip, 'vFA': vfa, 'Stuff+': stuffplus
                                },
                                index=[0])
        build_df = pd.concat([build_df,these_df])

    return(build_df)

def scrapeFG_hitters(fgid):
    fgurl = 'https://www.fangraphs.com/api/players/stats?playerid={}&position=OF'.format(fgid)
    response = requests.get(fgurl)

    # Check if request was successful
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
        
        wrc = x.get('wRC+')
        wrc = round(wrc,0)
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
        krate = round(strikeouts/pa,3)
        krate = f"{krate:.3f}"
        bbrate = round(walks/pa,3)
        bbrate = f"{bbrate:.3f}"
        swstr = x.get('SwStr%')
        swingrate = x.get('pfxSwing%')
        contactrate = x.get('pfxContact%')
        hits = singles+doubles+triples+homers
        r = x.get('R')
        rbi = x.get('RBI')

        avg = round(hits/ab,3)
        obp = round((hits+walks+hbp)/pa,3)
        slg = round(((singles)+(doubles*2)+(triples*3)+(homers*4))/ab,3)
        ops = obp+slg
        try:
            swingrate = f"{swingrate:.3f}"
        except:
            swingrate = '--'
        
        try:
            contactrate = f"{contactrate:.3f}"
        except:
            contactrate = '--'
        try:
            swstr = f"{swstr:.3f}"
        except:
            swstr = '--'
        

        these_df = pd.DataFrame({'Season': str(season), 'Team': teamshort, 'Level': level,
                                'Age': seasonage, 'G': g, 'AB': ab, 'AVG': round(hits/ab,3), 'OBP': round(obp,3),
                                'SLG': slg, 'OPS': ops, 'HR': homers, 'R': r, 'RBI': rbi,
                                'K%': krate, 'BB%': bbrate, 'SwStr%': swstr, 'Cont%': contactrate, 'Swing%': swingrate,
                                'wRC+': wrc, 
                                },
                                index=[0])
        build_df = pd.concat([build_df,these_df])

    return(build_df)

def main():
    # Sidebar
    with st.sidebar:
        st.markdown("<h2 style='color: white;'>MLB Player Lookup</h2>", unsafe_allow_html=True)
        name_input = st.text_input("Search Player", placeholder="Enter player name...")
        st.markdown("<p style='color: #EAF4F4;'>Enter a player's name to view their MLB profile</p>", unsafe_allow_html=True)

    # Main content
    st.markdown("<h1 class='title'>MLB Data Warehouse Player Lookup Tool</h1>", unsafe_allow_html=True)

    if name_input:
        with st.spinner("Fetching player data..."):
            result, error = get_player_id(name_input)

            if error:
                st.error(error)
            elif result:
                mlbid = result['MLBID']
                fgid = result['FGID']

                player_data = get_mlb_player_info(mlbid)
                check_pos = player_data.get('position')
                if check_pos == 'Pitcher':
                    fg_data = scrapeFG_pitchers(fgid)
                    #st.dataframe(fg_data,hide_index=True)
                else:
                    fg_data = scrapeFG_hitters(fgid)
                
                adv_data = loadAdvData(mlbid)
                gamelog = getGameLogs(int(mlbid))
                #hit_ja_skills = getSkills(mlbid)
                
                fscores = loadFScores(player_data['fullName'])
                if len(fscores)>0:
                    fContact = fscores['fContact'].iloc[0]
                    fPower = fscores['fPower'].iloc[0]
                    fSpeed = fscores['fSpeed'].iloc[0]
                    fDiscipline = fscores['fDiscipline'].iloc[0]
                else:
                    fContact=0
                    fPower=0
                    fSpeed=0
                    fDiscipline=0
                
                if player_data:
                    pinfo_pos = player_data.get('position')
                    pinfo_height = player_data.get('height')
                    pinfo_weight =  player_data.get('weight')
                    pinfo_hits =  player_data.get('bats')
                    pinfo_throws =  player_data.get('throws')
                    pinfo_debut =  player_data.get('debut')
                    # Player Card
                    with st.container():
                        st.markdown("<div class='player-card'>", unsafe_allow_html=True)
                        #col1, col2 = st.columns([1, 2])
                        col1, col2, col3, = st.columns([1,1,4.25])
                        
                        with col1:
                            st.image(get_player_image(mlbid), width=200, caption=player_data['fullName'])
                        
                        with col2:
                            st.subheader(player_data['fullName'])
                            st.markdown(f"""
                                <div style='line-height: 1.5; margin: 0; padding: 0;'>
                                    <b>{pinfo_pos}</b><br>
                                    <b>{pinfo_height}</b><br>
                                    <b>{pinfo_weight}</b><br>
                                    <b>Throws: {pinfo_throws}</b><br>
                                    <b>Debut: {pinfo_debut}</b><br>
                                </div>
                                """, unsafe_allow_html=True)
    
                        with col3:
                            st.markdown("<h4 style='color: white;'>2024-2025 Stats</h4>", unsafe_allow_html=True)
                            #mlb_abs = np.sum(fg_data[fg_data['Level']=='MLB']['AB'])
                            mlb_g = np.sum(fg_data[fg_data['Level']=='MLB']['G'])
                            if mlb_g < 5:
                                data24 = fg_data[(fg_data['Season'].isin(['2022','2023','2024','2025']))&(fg_data['Level'].isin(['MiLB','MLB']))]
                            else:
                                data24 = fg_data[(fg_data['Season'].isin(['2022','2023','2024','2025']))&(fg_data['Level'].isin(['MLB']))]
                            
                            data24 = data24.sort_values(by='Season',ascending=False)
                            st.dataframe(data24,hide_index=True)

                            col1, col2 = st.columns([1,1])
                            with col1:
                                st.markdown("<h4 style='color: white;'>2024-2025 Splits:</h4>", unsafe_allow_html=True)
                                #tableit = adv_data.pivot_table(index='BatterName',columns='Split',values=['K%','BB%','AVG','OBP','SLG','Cont%']).reset_index()
                                adv_data['ISO'] = adv_data['SLG']-adv_data['AVG']
                                showdf = adv_data[['Year','Level','Split','PA_flag','AVG','OBP','SLG','ISO','IsHomer','K%','BB%','Cont%']]
                                showdf = showdf[showdf['Split']!='All']                            
                                showdf = showdf.rename({'PA_flag':'PA','IsHomer':'HR'},axis=1)

                                # decide what to show
                                groupdata = showdf.groupby(['Level'],as_index=False)['PA'].sum()
                                try:
                                    mlb_pa = groupdata[groupdata['Level']=='MLB']['PA'].iloc[0]
                                except:
                                    mlb_pa = 0
                                if mlb_pa>99:
                                    player_level='Majors'
                                    showdf = showdf[showdf['Level']=='MLB']
                                elif mlb_pa<100:
                                    player_level='Minors'
                                    showdf = showdf[showdf['Level']=='Minors']
                                else:
                                    pass
                                # styled
                                styled_df = showdf.style.format({'PA': '{:.0f}','HR': '{:.0f}','AVG': '{:.3f}','OBP': '{:.3f}','SLG': '{:.3f}','ISO': '{:.3f}','K%': '{:.3f}','BB%': '{:.3f}','Cont%': '{:.3f}',})
                                #
                                st.dataframe(styled_df,hide_index=True)
                            
                            with col2:
                                st.markdown("<h4 style='color: white;'>Statcast Data:</h4>", unsafe_allow_html=True)
                                ### statcast stuff
                                launch_profile = adv_data[['Year','Level','Statcast BBE','GB%','LD%','FB%','SwtSpot%','EV 90']]
                                launch_profile = launch_profile.rename({'Statcast BBE': 'BBE'},axis=1)
                                launch_profile = launch_profile.drop_duplicates()
                                if player_level=='Majors':
                                    launch_profile = launch_profile[launch_profile['Level']=='MLB']
                                elif player_level=='Minors':
                                    launch_profile = launch_profile[launch_profile['Level']=='Minors']
                                else:
                                    pass

                                styled_df = launch_profile.style.format({'BBE': '{:.0f}','GB%': '{:.3f}','LD%': '{:.3f}','FB%': '{:.3f}','SwtSpot%': '{:.3f}','EV 90': '{:.1f}'})

                                st.dataframe(styled_df,hide_index=True)



                        # Additional Info
                        st.markdown("---")
                        stats_fig = create_stat_gauges(fContact, fPower, fSpeed, fDiscipline)
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.plotly_chart(stats_fig)
                        with col2:
                            st.markdown("<h4 style='color: white;'>Recent Game Log</h4>", unsafe_allow_html=True)
                            st.dataframe(gamelog, hide_index=True)

                        st.markdown("---")
                        st.markdown("</div>", unsafe_allow_html=True)

                else:
                    st.error("Unable to fetch player information")
    else:
        st.info("Please enter a player name in the sidebar to begin")

if __name__ == "__main__":
    main()