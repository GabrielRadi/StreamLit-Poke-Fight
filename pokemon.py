import streamlit as st
import requests as rq
import random

# Feito por: Eduardo Vieira Montagna, Gabriel Paz Ribeiro, Gustavo Fernandez Sanches, Otavio Augusto Milioni Costa e João Pedro Batista.

st.set_page_config(page_title="Pokémon API & Arena", layout="wide")
st.title("Pokémon API & Arena ⚔️")

# --- FUNÇÕES DE BUSCA E FILTRAGEM ---
@st.cache_data
def get_pokemon(nome):
    url = f"https://pokeapi.co/api/v2/pokemon/{nome.lower().strip()}"
    response = rq.get(url)
    if response.status_code == 200:
        return response.json()
    return None

@st.cache_data
def get_evolution_chain(species_url):
    response_especie = rq.get(species_url)
    if response_especie.status_code != 200:
        return []
    
    dados_especie = response_especie.json()
    url_evolucao = dados_especie['evolution_chain']['url']
    
    response_evolucao = rq.get(url_evolucao)
    if response_evolucao.status_code != 200:
        return []
        
    dados_evolucao = response_evolucao.json()
    cadeia = dados_evolucao['chain']
    
    lista_evolucoes = []
    def extrair_evolucoes(no_da_cadeia):
        lista_evolucoes.append(no_da_cadeia['species']['name'])
        for evolucao in no_da_cadeia['evolves_to']:
            extrair_evolucoes(evolucao)

    extrair_evolucoes(cadeia)
    return lista_evolucoes

@st.cache_data
def get_move_data(url):
    response = rq.get(url)
    if response.status_code == 200:
        return response.json()
    return None

@st.cache_data
def get_type_data(tipo_nome):
    url = f"https://pokeapi.co/api/v2/type/{tipo_nome}"
    response = rq.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def filtrar_golpes_level_up(pokemon_dados):
    golpes_permitidos = []
    for move_info in pokemon_dados['moves']:
        aprende_por_nivel = any(
            detalhe['move_learn_method']['name'] == 'level-up' 
            for detalhe in move_info['version_group_details']
        )
        if aprende_por_nivel:
            golpes_permitidos.append(move_info)
    return golpes_permitidos

def formatar_tipos(pokemon_dados):
    tipos = [t['type']['name'].title() for t in pokemon_dados['types']]
    return " / ".join(tipos)

# --- FUNÇÕES DE STATUS ---
def calcular_modificador_estagio(estagio, eh_precisao=False):
    if eh_precisao:
        numerador = max(3, 3 + estagio)
        denominador = max(3, 3 - estagio)
    else:
        numerador = max(2, 2 + estagio)
        denominador = max(2, 2 - estagio)
    return numerador / denominador

def extrair_atributos(pokemon_dados):
    return {s["stat"]["name"]: s["base_stat"] for s in pokemon_dados["stats"]}

def gerar_mensagem_acao(nome_atacante, nome_golpe, tipo_golpe, poder, dano_causado, texto_efetividade="", efeito_especial=""):
    msg = f"**{nome_atacante}** usou **{nome_golpe}** ({tipo_golpe.title()})!"
    if poder is None and dano_causado == 0:
        return f"✨ {msg} {efeito_especial}"
    elif dano_causado == 0:
        return f"🛡️ {msg} mas não teve efeito algum no alvo..."
    else:
        return f"⚔️ {msg} Causou **{dano_causado}** de dano!{texto_efetividade} {efeito_especial}"


# --- INICIALIZAR VARIÁVEIS DA BATALHA ---
if "batalha_ativa" not in st.session_state:
    st.session_state.batalha_ativa = False
if "log_batalha" not in st.session_state:
    st.session_state.log_batalha = []


aba_pokedex, aba_batalha = st.tabs(["📖 Pokédex", "⚔️ Arena de Batalha"])

@st.cache_data
def get_todos_os_nomes():
    url = "https://pokeapi.co/api/v2/pokemon?limit=1025"
    response = rq.get(url)
    if response.status_code == 200:
        dados = response.json()
        return sorted([p["name"] for p in dados["results"]])
    return []


# ==========================================
# ABA 1: POKÉDEX
# ==========================================
with aba_pokedex:
    st.subheader("Pesquise e Descubra Pokémon! 🔍")
    
    lista_pokemon = get_todos_os_nomes()
    
    search_query = st.selectbox(
        "Digite as primeiras letras ou selecione um Pokémon da lista:",
        options=lista_pokemon,
        index=lista_pokemon.index("pikachu") if "pikachu" in lista_pokemon else 0,
        format_func=lambda x: x.title().replace("-", " ")
    )

    if search_query:
        with st.spinner("Buscando detalhes do Pokémon, nya..."):
            pokemon_data = get_pokemon(search_query)
            
            if pokemon_data:
                poke_name = pokemon_data["name"].title()
                img_url = pokemon_data["sprites"]["other"]["official-artwork"]["front_default"]

                col1, col2 = st.columns(([1, 2]), gap="large")
                with col1:
                    if img_url:
                        st.image(img_url, width=200)
                    else:
                        st.image(pokemon_data["sprites"]["front_default"], width=150)
                with col2:
                    st.subheader(poke_name)
                    st.caption(f"**Tipos:** {formatar_tipos(pokemon_data)}")
                    
                    for stat in pokemon_data["stats"]:
                        stat_name = stat["stat"]["name"].replace("-", " ").title()
                        stat_value = stat["base_stat"]
                        st.progress(min(stat_value / 255, 1.0), text=f"{stat_name}: {stat_value}")
                    
                st.write("---")
                st.write("**Linha de Evolução:**")
                species_url = pokemon_data["species"]["url"]
                nomes_evolucoes = get_evolution_chain(species_url)
                
                if nomes_evolucoes:
                    cols_evolucao = st.columns(len(nomes_evolucoes))
                    for idx, nome_evo in enumerate(nomes_evolucoes):
                        with cols_evolucao[idx]:
                            dados_evo = get_pokemon(nome_evo)
                            if dados_evo and dados_evo["sprites"]["front_default"]:
                                st.image(dados_evo["sprites"]["front_default"], width=100)
                                st.caption(nome_evo.title())
            else:
                st.error("Pokémon não encontrado. Verifique o nome e tente novamente!")

# ==========================================
# ABA 2: ARENA DE BATALHA 
# ==========================================
with aba_batalha:
    if not st.session_state.batalha_ativa:
        st.header("Prepare seus Pokémon!")
        
        lista_pokemon = get_todos_os_nomes()
        
        col_lutador1, col_vs, col_lutador2 = st.columns([2, 1, 2])
        
        with col_lutador1:
            p1_index = lista_pokemon.index("gengar") if "gengar" in lista_pokemon else 0
            poke1_nome = st.selectbox(
                "Lutador 1:", 
                options=lista_pokemon, 
                index=p1_index, 
                key="p1_select",
                format_func=lambda x: x.title().replace("-", " ")
            )
        with col_vs:
            st.markdown("<h2 style='text-align: center; margin-top: 30px;'>VS</h2>", unsafe_allow_html=True)
        with col_lutador2:
            p2_index = lista_pokemon.index("ninetales") if "ninetales" in lista_pokemon else 0
            poke2_nome = st.selectbox(
                "Lutador 2:", 
                options=lista_pokemon, 
                index=p2_index, 
                key="p2_select",
                format_func=lambda x: x.title().replace("-", " ")
            )

        poke1_dados = get_pokemon(poke1_nome) if poke1_nome else None
        poke2_dados = get_pokemon(poke2_nome) if poke2_nome else None

        if poke1_dados and poke2_dados:
            st.write("---")
            st.subheader("Escolha até 4 golpes para cada lutador!")
            
            golpes_p1 = filtrar_golpes_level_up(poke1_dados)
            golpes_p2 = filtrar_golpes_level_up(poke2_dados)
            
            dict_golpes_p1 = {m["move"]["name"].replace("-", " ").title(): m for m in golpes_p1}
            dict_golpes_p2 = {m["move"]["name"].replace("-", " ").title(): m for m in golpes_p2}
            
            col_golpes1, col_golpes2 = st.columns(2)
            
            with col_golpes1:
                st.caption(f"**Tipos:** {formatar_tipos(poke1_dados)}")
                escolhas_p1 = st.multiselect(
                    f"Golpes do {poke1_dados['name'].title()}:", 
                    options=list(dict_golpes_p1.keys()), 
                    max_selections=4
                )
            
            with col_golpes2:
                st.caption(f"**Tipos:** {formatar_tipos(poke2_dados)}")
                escolhas_p2 = st.multiselect(
                    f"Golpes do {poke2_dados['name'].title()}:", 
                    options=list(dict_golpes_p2.keys()), 
                    max_selections=4
                )

            st.write("---")
            if st.button("Iniciar Batalha! 💥", use_container_width=True):
                if len(escolhas_p1) > 0 and len(escolhas_p2) > 0:
                    with st.spinner("Preparando a Arena, nya..."):
                        
                        st.session_state.p1 = poke1_dados
                        st.session_state.p2 = poke2_dados
                        
                        st.session_state.stats1 = extrair_atributos(poke1_dados)
                        st.session_state.stats2 = extrair_atributos(poke2_dados)
                        
                        st.session_state.hp1 = st.session_state.stats1["hp"] * 4
                        st.session_state.hp_max1 = st.session_state.hp1
                        st.session_state.hp2 = st.session_state.stats2["hp"] * 4
                        st.session_state.hp_max2 = st.session_state.hp2
                        
                        estagios_iniciais = {"attack": 0, "defense": 0, "special-attack": 0, "special-defense": 0, "speed": 0, "accuracy": 0}
                        st.session_state.estagios1 = estagios_iniciais.copy()
                        st.session_state.estagios2 = estagios_iniciais.copy()
                        
                        st.session_state.moves1 = [dict_golpes_p1[nome] for nome in escolhas_p1]
                        st.session_state.moves2 = [dict_golpes_p2[nome] for nome in escolhas_p2]
                        
                        st.session_state.status1 = None  
                        st.session_state.status2 = None
                        st.session_state.sono_turnos1 = 0 
                        st.session_state.sono_turnos2 = 0
                        
                        st.session_state.toxic_turnos1 = 0
                        st.session_state.toxic_turnos2 = 0
                        
                        st.session_state.ultimo_move1 = None
                        st.session_state.ultimo_move2 = None
                        st.session_state.disable1 = None       
                        st.session_state.disable2 = None       
                        st.session_state.disable_turnos1 = 0
                        st.session_state.disable_turnos2 = 0
                        
                        st.session_state.confuso1 = False  
                        st.session_state.confuso2 = False
                        st.session_state.confuso_turnos1 = 0
                        st.session_state.confuso_turnos2 = 0
                        
                        st.session_state.clima = "Normal"
                        st.session_state.clima_turnos = 0
                        
                        st.session_state.turno = 1
                        st.session_state.turnos_extras = 0
                        st.session_state.log_batalha = ["A batalha começou! ⚡"]
                        st.session_state.batalha_ativa = True
                        st.rerun()
                else:
                    st.warning("Escolha pelo menos 1 golpe para cada Pokémon antes de lutar")
                    
    else:
        st.header("Arena de Batalha ⚔️")
        
        p1 = st.session_state.p1
        p2 = st.session_state.p2
        
        if st.session_state.clima == "Chuva":
            st.info(f"🌧️ **Clima Atual: Dança da Chuva activa!** Golpes de Água fortalecidos e Fogo enfraquecidos.")
            
        col_arena1, col_arena2 = st.columns(2)
        
        emojis_status = {"Envenenado": "🤢", "Toxic": "☣️", "Paralisado": "⚡", "Dormindo": "💤", "Queimado": "🔥", "Congelado": "❄️"}
        
        with col_arena1:
            st.image(p1["sprites"]["front_default"], width=150)
            status_txt1 = ""
            if st.session_state.status1 in emojis_status:
                status_txt1 += f" {emojis_status[st.session_state.status1]} [{st.session_state.status1}]"
            if st.session_state.confuso1: status_txt1 += " 😵‍💫 [Confuso]"
            if st.session_state.disable1: status_txt1 += f" ❌ [Disable: {st.session_state.disable1}]"
                
            st.write(f"**{p1['name'].title()}** ({formatar_tipos(p1)}){status_txt1}")
            hp_pct1 = max(0.0, st.session_state.hp1 / st.session_state.hp_max1)
            st.progress(hp_pct1, text=f"HP: {max(0, st.session_state.hp1)}/{st.session_state.hp_max1}")
            
        with col_arena2:
            st.image(p2["sprites"]["front_default"], width=150)
            status_txt2 = ""
            if st.session_state.status2 in emojis_status:
                status_txt2 += f" {emojis_status[st.session_state.status2]} [{st.session_state.status2}]"
            if st.session_state.confuso2: status_txt2 += " 😵‍💫 [Confuso]"
            if st.session_state.disable2: status_txt2 += f" ❌ [Disable: {st.session_state.disable2}]"
                
            st.write(f"**{p2['name'].title()}** ({formatar_tipos(p2)}){status_txt2}")
            hp_pct2 = max(0.0, st.session_state.hp2 / st.session_state.hp_max2)
            st.progress(hp_pct2, text=f"HP: {max(0, st.session_state.hp2)}/{st.session_state.hp_max2}")

        st.write("---")
        
        if st.session_state.hp1 <= 0 or st.session_state.hp2 <= 0:
            vencedor = p1['name'].title() if st.session_state.hp2 <= 0 else p2['name'].title()
            st.success(f"🏆 O vencedor é **{vencedor}**! Nya!")
            st.balloons()
            
            if st.button("Jogar Novamente 🔄"):
                st.session_state.batalha_ativa = False
                st.rerun()
        else:
            jogador_atual = 1 if st.session_state.turno == 1 else 2
            nome_atacante = p1['name'].title() if jogador_atual == 1 else p2['name'].title()
            poke_defensor = p2 if jogador_atual == 1 else p1
            movimentos_atuais = st.session_state.moves1 if jogador_atual == 1 else st.session_state.moves2
            
            st.subheader(f"Vez do {nome_atacante} atacar!")
            
            opcoes_golpes = {m["move"]["name"].replace("-", " ").title(): m["move"]["url"] for m in movimentos_atuais}
            
            col_golpe, col_btn = st.columns([3, 1])
            with col_golpe:
                golpe_escolhido = st.selectbox("Escolha seu golpe:", list(opcoes_golpes.keys()))
            
            with col_btn:
                st.write("")
                st.write("")
                btn_atacar = st.button("Atacar! ⚡", use_container_width=True)
                
            if btn_atacar:
                golpe_bloqueado = st.session_state.disable1 if jogador_atual == 1 else st.session_state.disable2
                
                if golpe_bloqueado and golpe_escolhido.lower().strip() == golpe_bloqueado.lower().strip():
                    st.error(f"❌ O movimento **{golpe_escolhido}** está desativado por conta do Disable! Escolha outro movimento")
                    st.session_state.log_batalha.insert(0, f"⚠️ **{nome_atacante}** tentou usar **{golpe_escolhido}**, mas o golpe está desativado pelo Disable!")
                    pode_atacar = False
                    st.session_state.turno = 2 if jogador_atual == 1 else 1
                    st.rerun()
                else:
                    pode_atacar = True

                url_do_golpe = opcoes_golpes[golpe_escolhido]
                dados_do_golpe = get_move_data(url_do_golpe)
                
                nome_interno_golpe = dados_do_golpe["name"] if dados_do_golpe else ""
                tipo_do_golpe = dados_do_golpe["type"]["name"] if dados_do_golpe else "normal"
                poder = dados_do_golpe.get("power")
                precisao_base = dados_do_golpe.get("accuracy")
                classe_dano = dados_do_golpe.get("damage_class", {}).get("name", "physical")
                
                estagios_atacante = st.session_state.estagios1 if jogador_atual == 1 else st.session_state.estagios2
                estagios_defensor = st.session_state.estagios2 if jogador_atual == 1 else st.session_state.estagios1
                stats_atacante = st.session_state.stats1 if jogador_atual == 1 else st.session_state.stats2
                stats_defensor = st.session_state.stats2 if jogador_atual == 1 else st.session_state.stats1
                
                status_atkr = st.session_state.status1 if jogador_atual == 1 else st.session_state.status2
                confuso_atkr = st.session_state.confuso1 if jogador_atual == 1 else st.session_state.confuso2
                confuso_turnos = st.session_state.confuso_turnos1 if jogador_atual == 1 else st.session_state.confuso_turnos2
                sono_turnos = st.session_state.sono_turnos1 if jogador_atual == 1 else st.session_state.sono_turnos2

                if pode_atacar and status_atkr == "Congelado":
                    if random.randint(1, 100) <= 20: 
                        if jogador_atual == 1: st.session_state.status1 = None
                        else: st.session_state.status2 = None
                        st.session_state.log_batalha.insert(0, f"☀️ **{nome_atacante}** se derreteu e conseguiu se mover!")
                        status_atkr = None
                    else:
                        st.session_state.log_batalha.insert(0, f"❄️ **{nome_atacante}** está congelado! Não consegue se mover!")
                        pode_atacar = False

                if pode_atacar and status_atkr == "Dormindo":
                    if sono_turnos <= 0:
                        if jogador_atual == 1: st.session_state.status1 = None
                        else: st.session_state.status2 = None
                        st.session_state.log_batalha.insert(0, f"☀️ **{nome_atacante}** acordou!")
                        status_atkr = None
                    else:
                        if jogador_atual == 1: st.session_state.sono_turnos1 -= 1
                        else: st.session_state.sono_turnos2 -= 1
                        st.session_state.log_batalha.insert(0, f"💤 **{nome_atacante}** está dormindo profundamente...")
                        pode_atacar = False

                if pode_atacar and confuso_atkr and confuso_turnos <= 0:
                    if jogador_atual == 1: st.session_state.confuso1 = False
                    else: st.session_state.confuso2 = False
                    st.session_state.log_batalha.insert(0, f"✨ **{nome_atacante}** se livrou da confusão!")
                    confuso_atkr = False

                if pode_atacar and status_atkr == "Paralisado" and random.randint(1, 100) <= 25:
                    st.session_state.log_batalha.insert(0, f"⚡ **{nome_atacante}** está totalmente paralisado! Não conseguiu se mover!")
                    pode_atacar = False

                if pode_atacar and confuso_atkr:
                    if jogador_atual == 1: st.session_state.confuso_turnos1 -= 1
                    else: st.session_state.confuso_turnos2 -= 1
                    
                    st.session_state.log_batalha.insert(0, f"😵‍💫 **{nome_atacante}** está confuso...")
                    if random.randint(1, 100) <= 33:
                        atk_real = stats_atacante["attack"] * calcular_modificador_estagio(estagios_atacante["attack"])
                        if status_atkr == "Queimado": atk_real *= 0.5 
                        def_real = stats_atacante["defense"] * calcular_modificador_estagio(estagios_atacante["defense"])
                        dano_auto = int(((22 * 40 * (atk_real / def_real)) / 50) + 2)
                        
                        if jogador_atual == 1: st.session_state.hp1 -= dano_auto
                        else: st.session_state.hp2 -= dano_auto
                        
                        st.session_state.log_batalha.insert(0, f"💥 Ficou tão confuso que bateu em si mesmo causando **{dano_auto}** de dano!")
                        pode_atacar = False

                if pode_atacar:
                    acertou = True
                    if precisao_base is not None:
                        mod_acc = calcular_modificador_estagio(estagios_atacante["accuracy"], eh_precisao=True)
                        chance_acerto = precisao_base * mod_acc
                        if random.randint(1, 100) > chance_acerto:
                            acertou = False

                    if not acertou:
                        mensagem_log = f"💨 **{nome_atacante}** tentou usar **{golpe_escolhido}**, mas errou o ataque!"
                        st.session_state.log_batalha.insert(0, mensagem_log)
                    else:
                        if jogador_atual == 1: st.session_state.ultimo_move1 = golpe_escolhido
                        else: st.session_state.ultimo_move2 = golpe_escolhido
                        
                        multiplicador = 1.0
                        texto_efetividade = ""
                        efeito_especial = ""
                        dano_causado = 0
                        mensagens_status = []
                        
                        status_defensor_atual = st.session_state.status2 if jogador_atual == 1 else st.session_state.status1
                        if status_defensor_atual == "Congelado" and tipo_do_golpe == "fire":
                            if jogador_atual == 1: st.session_state.status2 = None
                            else: st.session_state.status1 = None
                            efeito_especial += " 🔥 O calor do golpe derreteu o gelo do oponente!"

                        mudancas_stats = dados_do_golpe.get("stat_changes", [])
                        if mudancas_stats:
                            alvo_do_golpe = dados_do_golpe.get("target", {}).get("name", "")
                            alvo_estagios = estagios_atacante if "user" in alvo_do_golpe else estagios_defensor
                            
                            for mudanca in mudancas_stats:
                                nome_stat = mudanca["stat"]["name"]
                                valor_mudanca = mudanca["change"]
                                if nome_stat in alvo_estagios:
                                    alvo_estagios[nome_stat] = max(-6, min(6, alvo_estagios[nome_stat] + valor_mudanca))
                                    direcao = "caiu" if valor_mudanca < 0 else "subiu"
                                    mensagens_status.append(f"[{nome_stat.title()} {direcao}!]")
                                    
                            if mensagens_status:
                                efeito_especial += " " + " ".join(mensagens_status)
                            # STATUS DE EFEITO SENDO APLICADOS
                        if poder is None:
                            if nome_interno_golpe == "rest":
                                if jogador_atual == 1:
                                    st.session_state.hp1 = st.session_state.hp_max1
                                    st.session_state.status1 = "Dormindo"
                                    st.session_state.sono_turnos1 = 2
                                else:
                                    st.session_state.hp2 = st.session_state.hp_max2
                                    st.session_state.status2 = "Dormindo"
                                    st.session_state.sono_turnos2 = 2
                                efeito_especial += " recuperou toda a vida e caiu no sono! 🛌"

                            elif nome_interno_golpe == "disable":
                                ultimo_do_alvo = st.session_state.ultimo_move2 if jogador_atual == 1 else st.session_state.ultimo_move1
                                if ultimo_do_alvo:
                                    if jogador_atual == 1:
                                        st.session_state.disable2 = ultimo_do_alvo
                                        st.session_state.disable_turnos2 = 3
                                    else:
                                        st.session_state.disable1 = ultimo_do_alvo
                                        st.session_state.disable_turnos1 = 3
                                    efeito_especial += f" Desativou temporariamente o golpe **{ultimo_do_alvo}** do rival por 3 turnos! ❌"
                                else:
                                    efeito_especial += " mas falhou porque o oponente ainda não executou nenhum movimento"

                            elif "sleep-powder" in nome_interno_golpe or "hypnosis" in nome_interno_golpe or "spore" in nome_interno_golpe:
                                turnos_aleatorios = random.randint(2, 3)
                                if jogador_atual == 1:
                                    st.session_state.status2 = "Dormindo"
                                    st.session_state.sono_turnos2 = turnos_aleatorios
                                else:
                                    st.session_state.status1 = "Dormindo"
                                    st.session_state.sono_turnos1 = turnos_aleatorios
                                efeito_especial += f" Fez o oponente pegar no sono por {turnos_aleatorios} turnos! 💤"

                            elif "stun-spore" in nome_interno_golpe or "thunder-wave" in nome_interno_golpe:
                                if jogador_atual == 1: st.session_state.status2 = "Paralisado"
                                else: st.session_state.status1 = "Paralisado"
                                efeito_especial += " O oponente foi paralisado! ⚡"
                            
                            elif "will-o-wisp" in nome_interno_golpe:
                                if jogador_atual == 1: st.session_state.status2 = "Queimado"
                                else: st.session_state.status1 = "Queimado"
                                efeito_especial += " O oponente foi queimado! 🔥"

                            elif "powder-snow" in nome_interno_golpe or "blizzard" in nome_interno_golpe or "ice-beam" in nome_interno_golpe:
                                if jogador_atual == 1: st.session_state.status2 = "Congelado"
                                else: st.session_state.status1 = "Congelado"
                                efeito_especial += " O oponente ficou congelado! ❄️"

                            elif "confuse" in nome_interno_golpe or "supersonic" in nome_interno_golpe:
                                if jogador_atual == 1:
                                    st.session_state.confuso2 = True
                                    st.session_state.confuso_turnos2 = random.randint(2, 4)
                                else:
                                    st.session_state.confuso1 = True
                                    st.session_state.confuso_turnos1 = random.randint(2, 4)
                                efeito_especial += " O oponente ficou confuso! 😵‍💫"
                                
                            elif nome_interno_golpe == "toxic":
                                status_alvo = st.session_state.status2 if jogador_atual == 1 else st.session_state.status1
                                if status_alvo is None:
                                    if jogador_atual == 1:
                                        st.session_state.status2 = "Toxic"
                                        st.session_state.toxic_turnos2 = 1
                                    else:
                                        st.session_state.status1 = "Toxic"
                                        st.session_state.toxic_turnos1 = 1
                                    efeito_especial += " O oponente foi gravemente envenenado pelo veneno corrosivo! ☣️"
                                else:
                                    efeito_especial += " mas falhou porque o alvo já possui uma condição!"
                                
                            elif "poison" in nome_interno_golpe or "smog" in nome_interno_golpe:
                                status_alvo = st.session_state.status2 if jogador_atual == 1 else st.session_state.status1
                                if status_alvo is None:
                                    if jogador_atual == 1: st.session_state.status2 = "Envenenado"
                                    else: st.session_state.status1 = "Envenenado"
                                    efeito_especial += " O oponente foi envenenado! 🤢"
                                    
                            elif nome_interno_golpe == "rain-dance":
                                st.session_state.clima = "Chuva"
                                st.session_state.clima_turnos = 5
                                efeito_especial += " Uma tempestade começou! 🌧️"
                                
                            mensagem_log = gerar_mensagem_acao(nome_atacante, golpe_escolhido, tipo_do_golpe, poder, 0, "", efeito_especial)
                        else:
                            tipos_defensor = [t["type"]["name"] for t in poke_defensor["types"]]
                            dados_fraquezas = get_type_data(tipo_do_golpe)
                            
                            if dados_fraquezas:
                                relacoes = dados_fraquezas["damage_relations"]
                                for t_def in tipos_defensor:
                                    if t_def in [t["name"] for t in relacoes["double_damage_to"]]: multiplicador *= 2.0
                                    elif t_def in [t["name"] for t in relacoes["half_damage_to"]]: multiplicador *= 0.5
                                    elif t_def in [t["name"] for t in relacoes["no_damage_to"]]: multiplicador *= 0.0
                            
                            if st.session_state.clima == "Chuva":
                                if tipo_do_golpe == "water": multiplicador *= 1.5
                                elif tipo_do_golpe == "fire": multiplicador *= 0.5
                                    
                            if multiplicador > 1.0: texto_efetividade += " **Super efetivo! 💥**"
                            elif multiplicador < 1.0 and multiplicador > 0: texto_efetividade += " **Não foi muito efetivo... 🍃**"

                            if multiplicador > 0:
                                stat_atk = "special-attack" if classe_dano == "special" else "attack"
                                stat_def = "special-defense" if classe_dano == "special" else "defense"
                                
                                atk_real = stats_atacante[stat_atk] * calcular_modificador_estagio(estagios_atacante[stat_atk])
                                if stat_atk == "attack" and status_atkr == "Queimado": atk_real *= 0.5
                                    
                                def_real = stats_defensor[stat_def] * calcular_modificador_estagio(estagios_defensor[stat_def])
                                
                                dano_base = int(((22 * poder * (atk_real / def_real)) / 50) + 2)
                                dano_causado = int(dano_base * random.uniform(0.85, 1.0) * multiplicador)

                                if jogador_atual == 1: st.session_state.hp2 -= dano_causado
                                else: st.session_state.hp1 -= dano_causado
                                
                            if tipo_do_golpe == "fire" and poder is not None:
                                status_atual_defensor = st.session_state.status2 if jogador_atual == 1 else st.session_state.status1
                                if status_atual_defensor is None and random.randint(1, 100) <= 10:
                                    if jogador_atual == 1: st.session_state.status2 = "Queimado"
                                    else: st.session_state.status1 = "Queimado"
                                    efeito_especial += " 🔥 As chamas intensas deixaram uma queimadura no oponente!"
                                    
                            elif tipo_do_golpe == "ice" and poder is not None and random.randint(1, 100) <= 10:
                                if jogador_atual == 1 and not st.session_state.status2: st.session_state.status2 = "Congelado"
                                elif jogador_atual == 2 and not st.session_state.status1: st.session_state.status1 = "Congelado"
                                efeito_especial += " O frio extremo congelou o alvo! ❄️"

                            mensagem_log = gerar_mensagem_acao(nome_atacante, golpe_escolhido, tipo_do_golpe, poder, dano_causado, texto_efetividade, efeito_especial)

                        st.session_state.log_batalha.insert(0, mensagem_log)
                # DISABLED MOVESET
                if jogador_atual == 1 and st.session_state.disable1:
                    st.session_state.disable_turnos1 -= 1
                    if st.session_state.disable_turnos1 <= 0:
                        st.session_state.log_batalha.insert(0, f"✨ O efeito do Disable no **{p1['name'].title()}** sumiu! O movimento **{st.session_state.disable1}** foi liberado!")
                        st.session_state.disable1 = None
                elif jogador_atual == 2 and st.session_state.disable2:
                    st.session_state.disable_turnos2 -= 1
                    if st.session_state.disable_turnos2 <= 0:
                        st.session_state.log_batalha.insert(0, f"✨ O efeito do Disable no **{p2['name'].title()}** sumiu! O movimento **{st.session_state.disable2}** foi liberado!")
                        st.session_state.disable2 = None

                if st.session_state.status1 == "Envenenado" and st.session_state.hp1 > 0:
                    st.session_state.hp1 -= max(3, int(st.session_state.hp_max1 * 0.04))
                    st.session_state.log_batalha.insert(0, f"🤢 O **{p1['name'].title()}** sofreu dano pelo veneno!")
                if st.session_state.status2 == "Envenenado" and st.session_state.hp2 > 0:
                    st.session_state.hp2 -= max(3, int(st.session_state.hp_max2 * 0.04))
                    st.session_state.log_batalha.insert(0, f"🤢 O **{p2['name'].title()}** sofreu dano pelo veneno!")

                if st.session_state.status1 == "Toxic" and st.session_state.hp1 > 0:
                    turno_atual_tox = st.session_state.toxic_turnos1
                    pct_dano = 0.03 * turno_atual_tox
                    dano_tox = max(4, int(st.session_state.hp_max1 * pct_dano))
                    st.session_state.hp1 -= dano_tox
                    st.session_state.log_batalha.insert(0, f"☣️ O veneno do Toxic corre pelas veias do **{p1['name'].title()}**! Causou **{dano_tox}** de dano (Turno {turno_atual_tox}/5)!")
                    if turno_atual_tox >= 5:
                        st.session_state.status1 = None
                        st.session_state.toxic_turnos1 = 0
                        st.session_state.log_batalha.insert(0, f"✨ O efeito do Toxic no **{p1['name'].title()}** expirou naturalmente!")
                    else: st.session_state.toxic_turnos1 += 1

                if st.session_state.status2 == "Toxic" and st.session_state.hp2 > 0:
                    turno_atual_tox = st.session_state.toxic_turnos2
                    pct_dano = 0.03 * turno_atual_tox
                    dano_tox = max(4, int(st.session_state.hp_max2 * pct_dano))
                    st.session_state.hp2 -= dano_tox
                    st.session_state.log_batalha.insert(0, f"☣️ O veneno do Toxic corre pelas veias do **{p2['name'].title()}**! Causou **{dano_tox}** de dano (Turno {turno_atual_tox}/5)!")
                    if turno_atual_tox >= 5:
                        st.session_state.status2 = None
                        st.session_state.toxic_turnos2 = 0
                        st.session_state.log_batalha.insert(0, f"✨ O efeito do Toxic no **{p2['name'].title()}** expirou naturalmente!")
                    else: st.session_state.toxic_turnos2 += 1

                if st.session_state.status1 == "Queimado" and st.session_state.hp1 > 0:
                    st.session_state.hp1 -= max(4, int(st.session_state.hp_max1 * 0.06))
                    st.session_state.log_batalha.insert(0, f"🔥 O **{p1['name'].title()}** sofreu dano por queimadura!")
                if st.session_state.status2 == "Queimado" and st.session_state.hp2 > 0:
                    st.session_state.hp2 -= max(4, int(st.session_state.hp_max2 * 0.06))
                    st.session_state.log_batalha.insert(0, f"🔥 O **{p2['name'].title()}** sofreu dano por queimadura!")

                if st.session_state.clima != "Normal":
                    st.session_state.clima_turnos -= 1
                    if st.session_state.clima_turnos <= 0:
                        st.session_state.clima = "Normal"
                        st.session_state.log_batalha.insert(0, "☀️ O céu clareou e a chuva parou na arena!")

                speed_p1_real = st.session_state.stats1["speed"] * calcular_modificador_estagio(st.session_state.estagios1["speed"])
                speed_p2_real = st.session_state.stats2["speed"] * calcular_modificador_estagio(st.session_state.estagios2["speed"])
                
                if st.session_state.status1 == "Paralisado": speed_p1_real *= 0.5
                if st.session_state.status2 == "Paralisado": speed_p2_real *= 0.5
                
                speed_atacante = speed_p1_real if jogador_atual == 1 else speed_p2_real
                speed_defensor = speed_p2_real if jogador_atual == 1 else speed_p1_real
                
                if pode_atacar and speed_atacante >= speed_defensor * 4.0 and st.session_state.turnos_extras < 1:
                    st.session_state.turnos_extras += 1
                    st.session_state.log_batalha.insert(0, f"💨 A velocidade do **{nome_atacante}** é avassaladora! Conseguiu um turno extra por pura agilidade")
                else:
                    st.session_state.turno = 2 if jogador_atual == 1 else 1
                    st.session_state.turnos_extras = 0

                st.rerun()

        with st.expander("📝 Histórico da Batalha", expanded=True):
            for linha in st.session_state.log_batalha:
                st.write(linha)
                
        st.write("---")
        if st.button("Fugir da batalha 🏳️"):
            st.session_state.batalha_ativa = False
            st.rerun()
