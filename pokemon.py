import streamlit as st
import requests as rq
import random

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
        st.header("Prepare suas Equipes para a Batalha!")
        lista_pokemon = get_todos_os_nomes()

        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.subheader("🔴 Equipe 1")
            qtd_p1 = st.number_input("Quantidade de Pokémon (Equipe 1):", min_value=1, max_value=6, value=1, key="qtd_p1")
            
            time1_preparado = []
            for i in range(int(qtd_p1)):
                with st.expander(f"Pokémon #{i+1} - Equipe 1", expanded=(i==0)):
                    p_nome = st.selectbox(f"Escolha o Pokémon #{i+1}:", options=lista_pokemon, index=lista_pokemon.index("gengar") if "gengar" in lista_pokemon else 0, key=f"t1_p_{i}")
                    p_dados = get_pokemon(p_nome)
                    if p_dados:
                        golpes = filtrar_golpes_level_up(p_dados)
                        dict_golpes = {m["move"]["name"].replace("-", " ").title(): m for m in golpes}
                        escolhas = st.multiselect(f"Golpes de {p_dados['name'].title()}:", options=list(dict_golpes.keys()), max_selections=4, key=f"t1_g_{i}")
                        
                        if escolhas:
                            time1_preparado.append({
                                "dados": p_dados,
                                "moves": [dict_golpes[n] for n in escolhas],
                                "hp_max": extrair_atributos(p_dados)["hp"] * 4,
                                "hp": extrair_atributos(p_dados)["hp"] * 4,
                                "stats_base": extrair_atributos(p_dados),
                                "status": None,
                                "toxic_turnos": 0,
                                "sono_turnos": 0,
                                "confuso": False,
                                "confuso_turnos": 0,
                                "disable": None,
                                "disable_turnos": 0,
                                "ultimo_move": None,
                                "estagios": {"attack": 0, "defense": 0, "special-attack": 0, "special-defense": 0, "speed": 0, "accuracy": 0}
                            })

        with col_t2:
            st.subheader("🔵 Equipe 2")
            qtd_p2 = st.number_input("Quantidade de Pokémon (Equipe 2):", min_value=1, max_value=6, value=1, key="qtd_p2")
            
            time2_preparado = []
            for i in range(int(qtd_p2)):
                with st.expander(f"Pokémon #{i+1} - Equipe 2", expanded=(i==0)):
                    p_nome = st.selectbox(f"Escolha o Pokémon #{i+1}:", options=lista_pokemon, index=lista_pokemon.index("ninetales") if "ninetales" in lista_pokemon else 0, key=f"t2_p_{i}")
                    p_dados = get_pokemon(p_nome)
                    if p_dados:
                        golpes = filtrar_golpes_level_up(p_dados)
                        dict_golpes = {m["move"]["name"].replace("-", " ").title(): m for m in golpes}
                        escolhas = st.multiselect(f"Golpes de {p_dados['name'].title()}:", options=list(dict_golpes.keys()), max_selections=4, key=f"t2_g_{i}")
                        
                        if escolhas:
                            time2_preparado.append({
                                "dados": p_dados,
                                "moves": [dict_golpes[n] for n in escolhas],
                                "hp_max": extrair_atributos(p_dados)["hp"] * 4,
                                "hp": extrair_atributos(p_dados)["hp"] * 4,
                                "stats_base": extrair_atributos(p_dados),
                                "status": None,
                                "toxic_turnos": 0,
                                "sono_turnos": 0,
                                "confuso": False,
                                "confuso_turnos": 0,
                                "disable": None,
                                "disable_turnos": 0,
                                "ultimo_move": None,
                                "estagios": {"attack": 0, "defense": 0, "special-attack": 0, "special-defense": 0, "speed": 0, "accuracy": 0}
                            })

        st.write("---")
        if st.button("Iniciar Batalhas de Times! 💥", use_container_width=True):
            if len(time1_preparado) == int(qtd_p1) and len(time2_preparado) == int(qtd_p2):
                st.session_state.time1 = time1_preparado
                st.session_state.time2 = time2_preparado
                st.session_state.p1_ativo_idx = 0
                st.session_state.p2_ativo_idx = 0
                st.session_state.clima = "Normal"
                st.session_state.clima_turnos = 0
                st.session_state.turno = 1
                st.session_state.turnos_extras = 0
                st.session_state.log_batalha = ["A batalha de times começou! ⚡"]
                st.session_state.batalha_ativa = True
                st.rerun()
            else:
                st.warning("Por favor, selecione os Pokémon e pelo menos 1 golpe para cada um deles")
                    
    else:
        st.header("Arena de Batalha ⚔️")
        
        pk1 = st.session_state.time1[st.session_state.p1_ativo_idx]
        pk2 = st.session_state.time2[st.session_state.p2_ativo_idx]
        
        if st.session_state.clima == "Chuva":
            st.info(f"🌧️ **Clima Atual: Dança da Chuva ativa!**")
            
        col_arena1, col_arena2 = st.columns(2)
        emojis_status = {"Envenenado": "🤢", "Toxic": "☣️", "Paralisado": "⚡", "Dormindo": "💤", "Queimado": "🔥", "Congelado": "❄️"}
        
        with col_arena1:
            st.image(pk1["dados"]["sprites"]["front_default"], width=150)
            status_txt1 = f" {emojis_status[pk1['status']]}" if pk1['status'] else ""
            if pk1['confuso']: status_txt1 += " 😵‍💫"
            st.write(f"**{pk1['dados']['name'].title()}**{status_txt1} (Time 1)")
            st.progress(max(0.0, pk1["hp"] / pk1["hp_max"]), text=f"HP: {max(0, pk1['hp'])}/{pk1['hp_max']}")
            
            # Mostra Pokémons restantes no banco
            vivos_t1 = sum(1 for p in st.session_state.time1 if p["hp"] > 0)
            st.caption(f"Pokémons restantes: {vivos_t1}/{len(st.session_state.time1)}")
            
        with col_arena2:
            st.image(pk2["dados"]["sprites"]["front_default"], width=150)
            status_txt2 = f" {emojis_status[pk2['status']]}" if pk2['status'] else ""
            if pk2['confuso']: status_txt2 += " 😵‍💫"
            st.write(f"**{pk2['dados']['name'].title()}**{status_txt2} (Time 2)")
            st.progress(max(0.0, pk2["hp"] / pk2["hp_max"]), text=f"HP: {max(0, pk2['hp'])}/{pk2['hp_max']}")
            
            vivos_t2 = sum(1 for p in st.session_state.time2 if p["hp"] > 0)
            st.caption(f"Pokémons restantes: {vivos_t2}/{len(st.session_state.time2)}")

        st.write("---")
        
        # Checagem de Faint (Nocaute)
        if pk1["hp"] <= 0 or pk2["hp"] <= 0:
            if pk1["hp"] <= 0:
                st.warning(f"💀 **{pk1['dados']['name'].title()}** da Equipe 1 desmaiou!")
                opcoes_troca = [i for i, p in enumerate(st.session_state.time1) if p["hp"] > 0]
                if opcoes_troca:
                    proximo = st.selectbox("Escolha quem vai entrar para lutar:", opcoes_troca, format_func=lambda idx: st.session_state.time1[idx]["dados"]["name"].title())
                    if st.button("Enviar para o Combate 👟"):
                        pk1["estagios"] = {"attack": 0, "defense": 0, "special-attack": 0, "special-defense": 0, "speed": 0, "accuracy": 0}
                        pk1["confuso"] = False
                        st.session_state.p1_ativo_idx = proximo
                        st.session_state.log_batalha.insert(0, f"🔄 Equipe 1 enviou **{st.session_state.time1[proximo]['dados']['name'].title()}**!")
                        st.rerun()
                else:
                    st.success("🏆 **A Equipe 2 é a grande vencedora da partida!**")
                    st.balloons()
                    if st.button("Voltar ao Menu 🔄"): st.session_state.batalha_ativa = False; st.rerun()
            
            elif pk2["hp"] <= 0:
                st.warning(f"💀 **{pk2['dados']['name'].title()}** da Equipe 2 desmaiou!")
                opcoes_troca = [i for i, p in enumerate(st.session_state.time2) if p["hp"] > 0]
                if opcoes_troca:
                    proximo = st.selectbox("Escolha quem vai entrar para lutar:", opcoes_troca, format_func=lambda idx: st.session_state.time2[idx]["dados"]["name"].title())
                    if st.button("Enviar para o Combate 👟"):
                        pk2["estagios"] = {"attack": 0, "defense": 0, "special-attack": 0, "special-defense": 0, "speed": 0, "accuracy": 0}
                        pk2["confuso"] = False
                        st.session_state.p2_ativo_idx = proximo
                        st.session_state.log_batalha.insert(0, f"🔄 Equipe 2 enviou **{st.session_state.time2[proximo]['dados']['name'].title()}**!")
                        st.rerun()
                else:
                    st.success("🏆 **A Equipe 1 é a grande vencedora da partida!** ")
                    st.balloons()
                    if st.button("Voltar ao Menu 🔄"): st.session_state.batalha_ativa = False; st.rerun()
        else:
            # Fluxo normal de turnos
            jogador_atual = st.session_state.turno
            nome_atacante = pk1['dados']['name'].title() if jogador_atual == 1 else pk2['dados']['name'].title()
            pk_atkr = pk1 if jogador_atual == 1 else pk2
            pk_defr = pk2 if jogador_atual == 1 else pk1
            time_do_jogador = st.session_state.time1 if jogador_atual == 1 else st.session_state.time2
            
            st.subheader(f"Vez de: **Equipe {jogador_atual}** ({nome_atacante})")
            
            aba_acao_atk, aba_acao_troca = st.tabs(["⚔️ Escolher Golpe", "🔄 Trocar Pokémon"])
            
            with aba_acao_atk:
                opcoes_golpes = {m["move"]["name"].replace("-", " ").title(): m["move"]["url"] for m in pk_atkr["moves"]}
                col_golpe, col_btn = st.columns([3, 1])
                with col_golpe:
                    golpe_escolhido = st.selectbox("Selecione o ataque:", list(opcoes_golpes.keys()), key=f"gk_{st.session_state.turno}")
                with col_btn:
                    st.write(""); st.write("")
                    btn_atacar = st.button("Atacar! ⚡", use_container_width=True, key=f"btn_atk_{st.session_state.turno}")
            
            with aba_acao_troca:
                # Filtro de Pokemons vivos
                banco_disponivel = [i for i, p in enumerate(time_do_jogador) if p["hp"] > 0 and i != (st.session_state.p1_ativo_idx if jogador_atual == 1 else st.session_state.p2_ativo_idx)]
                if banco_disponivel:
                    p_para_trocar = st.selectbox("Escolha o Pokémon do banco:", banco_disponivel, format_func=lambda idx: f"{time_do_jogador[idx]['dados']['name'].title()} (HP: {time_do_jogador[idx]['hp']}/{time_do_jogador[idx]['hp_max']})")
                    btn_trocar = st.button("Executar Troca 🔄", use_container_width=True)
                else:
                    st.write("Você não tem mais Pokemons usaveis!")
                    btn_trocar = False

            # --- LÓGICA DO BOTÃO DE TROCA ---
            if btn_trocar:
                # Reseta buffs de status voláteis
                pk_atkr["estagios"] = {"attack": 0, "defense": 0, "special-attack": 0, "special-defense": 0, "speed": 0, "accuracy": 0}
                pk_atkr["confuso"] = False
                
                if jogador_atual == 1:
                    st.session_state.p1_ativo_idx = p_para_trocar
                    st.session_state.log_batalha.insert(0, f"🔄 **Equipe 1** chamou {nome_atacante} de volta e enviou **{st.session_state.time1[p_para_trocar]['dados']['name'].title()}**!")
                    st.session_state.turno = 2
                else:
                    st.session_state.p2_ativo_idx = p_para_trocar
                    st.session_state.log_batalha.insert(0, f"🔄 **Equipe 2** chamou {nome_atacante} de volta e enviou **{st.session_state.time2[p_para_trocar]['dados']['name'].title()}**!")
                    st.session_state.turno = 1
                st.rerun()

            # --- LÓGICA DO ATAQUE ---
            if btn_atacar:
                pode_atacar = True
                golpe_bloqueado = pk_atkr["disable"]
                
                if golpe_bloqueado and golpe_escolhido.lower().strip() == golpe_bloqueado.lower().strip():
                    st.error(f"❌ O movimento **{golpe_escolhido}** está desativado por Disable!")
                    pode_atacar = False
                    st.session_state.turno = 2 if jogador_atual == 1 else 1
                    st.rerun()

                url_do_golpe = opcoes_golpes[golpe_escolhido]
                dados_do_golpe = get_move_data(url_do_golpe)
                
                nome_interno_golpe = dados_do_golpe["name"] if dados_do_golpe else ""
                tipo_do_golpe = dados_do_golpe["type"]["name"] if dados_do_golpe else "normal"
                poder = dados_do_golpe.get("power")
                precisao_base = dados_do_golpe.get("accuracy")
                classe_dano = dados_do_golpe.get("damage_class", {}).get("name", "physical")
                
                # Aplicações usando as variáveis do dicionário do Pokémon ativo
                if pode_atacar and pk_atkr["status"] == "Congelado":
                    if random.randint(1, 100) <= 20: 
                        pk_atkr["status"] = None
                        st.session_state.log_batalha.insert(0, f"☀️ **{nome_atacante}** se derreteu!")
                    else:
                        st.session_state.log_batalha.insert(0, f"❄️ **{nome_atacante}** está congelado!")
                        pode_atacar = False

                if pode_atacar and pk_atkr["status"] == "Dormindo":
                    if pk_atkr["sono_turnos"] <= 0:
                        pk_atkr["status"] = None
                        st.session_state.log_batalha.insert(0, f"☀️ **{nome_atacante}** acordou!")
                    else:
                        pk_atkr["sono_turnos"] -= 1
                        st.session_state.log_batalha.insert(0, f"💤 **{nome_atacante}** está dormindo...")
                        pode_atacar = False

                if pode_atacar and pk_atkr["status"] == "Paralisado" and random.randint(1, 100) <= 25:
                    st.session_state.log_batalha.insert(0, f"⚡ **{nome_atacante}** está paralisado!")
                    pode_atacar = False

                if pode_atacar and pk_atkr["confuso"]:
                    if pk_atkr["confuso_turnos"] <= 0:
                        pk_atkr["confuso"] = False
                        st.session_state.log_batalha.insert(0, f"✨ **{nome_atacante}** se livrou da confusão!")
                    else:
                        pk_atkr["confuso_turnos"] -= 1
                        st.session_state.log_batalha.insert(0, f"😵‍💫 **{nome_atacante}** está confuso...")
                        if random.randint(1, 100) <= 33:
                            atk_real = pk_atkr["stats_base"]["attack"] * calcular_modificador_estagio(pk_atkr["estagios"]["attack"])
                            if pk_atkr["status"] == "Queimado": atk_real *= 0.5 
                            def_real = pk_atkr["stats_base"]["defense"] * calcular_modificador_estagio(pk_atkr["estagios"]["defense"])
                            dano_auto = int(((22 * 40 * (atk_real / def_real)) / 50) + 2)
                            pk_atkr["hp"] -= dano_auto
                            st.session_state.log_batalha.insert(0, f"💥 Bateu em si mesmo causando **{dano_auto}** de dano!")
                            pode_atacar = False

                if pode_atacar:
                    acertou = True
                    if precisao_base is not None:
                        mod_acc = calcular_modificador_estagio(pk_atkr["estagios"]["accuracy"], eh_precisao=True)
                        if random.randint(1, 100) > (precisao_base * mod_acc): acertou = False

                    if not acertou:
                        st.session_state.log_batalha.insert(0, f"💨 **{nome_atacante}** errou o ataque **{golpe_escolhido}**!")
                    else:
                        pk_atkr["ultimo_move"] = golpe_escolhido
                        multiplicador = 1.0
                        texto_efetividade = ""
                        efeito_especial = ""
                        
                        # Efeito de Danos e Alterações de Status
                        if poder is None:
                            if nome_interno_golpe == "rest":
                                pk_atkr["hp"] = pk_atkr["hp_max"]
                                pk_atkr["status"] = "Dormindo"
                                pk_atkr["sono_turnos"] = 2
                                efeito_especial += " recuperou toda a vida e caiu no sono! 🛌"
                            elif nome_interno_golpe == "disable" and pk_defr["ultimo_move"]:
                                pk_defr["disable"] = pk_defr["ultimo_move"]
                                pk_defr["disable_turnos"] = 3
                                efeito_especial += f" Desativou o golpe **{pk_defr['ultimo_move']}** do rival! ❌"
                            elif "sleep-powder" in nome_interno_golpe or "hypnosis" in nome_interno_golpe:
                                if not pk_defr["status"]:
                                    pk_defr["status"] = "Dormindo"; pk_defr["sono_turnos"] = random.randint(2,3)
                                    efeito_especial += " Fez o oponente dormir! 💤"
                            elif "stun-spore" in nome_interno_golpe or "thunder-wave" in nome_interno_golpe:
                                if not pk_defr["status"]: pk_defr["status"] = "Paralisado"; efeito_especial += " Paralisou o rival! ⚡"
                            elif "will-o-wisp" in nome_interno_golpe:
                                if not pk_defr["status"]: pk_defr["status"] = "Queimado"; efeito_especial += " Queimou o rival! 🔥"
                            elif nome_interno_golpe == "toxic":
                                if not pk_defr["status"]: pk_defr["status"] = "Toxic"; pk_defr["toxic_turnos"] = 1; efeito_especial += " Envenenou gravemente (Toxic)! ☣️"
                            elif "confuse" in nome_interno_golpe:
                                pk_defr["confuso"] = True; pk_defr["confuso_turnos"] = random.randint(2,4)
                                efeito_especial += " Deixou o oponente confuso! 😵‍💫"
                            elif nome_interno_golpe == "rain-dance":
                                st.session_state.clima = "Chuva"; st.session_state.clima_turnos = 5
                                efeito_especial += " A chuva começou! 🌧️"
                            
                            mensagem_log = gerar_mensagem_acao(nome_atacante, golpe_escolhido, tipo_do_golpe, poder, 0, "", efeito_especial)
                        else:
                            # Cálculo de Dano
                            tipos_defensor = [t["type"]["name"] for t in pk_defr["dados"]["types"]]
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
                            elif 0 < multiplicador < 1.0: texto_efetividade += " **Não foi muito efetivo... 🍃**"
                            
                            if multiplicador > 0:
                                stat_atk = "special-attack" if classe_dano == "special" else "attack"
                                stat_def = "special-defense" if classe_dano == "special" else "defense"
                                atk_real = pk_atkr["stats_base"][stat_atk] * calcular_modificador_estagio(pk_atkr["estagios"][stat_atk])
                                if stat_atk == "attack" and pk_atkr["status"] == "Queimado": atk_real *= 0.5
                                def_real = pk_defr["stats_base"][stat_def] * calcular_modificador_estagio(pk_defr["estagios"][stat_def])
                                
                                dano_base = int(((22 * poder * (atk_real / def_real)) / 50) + 2)
                                dano_causado = int(dano_base * random.uniform(0.85, 1.0) * multiplicador)
                                pk_defr["hp"] -= dano_causado
                            else:
                                dano_causado = 0
                                texto_efetividade += " Não surtiu efeito..."

                            mensagem_log = gerar_mensagem_acao(nome_atacante, golpe_escolhido, tipo_do_golpe, poder, dano_causado, texto_efetividade, efeito_especial)
                        st.session_state.log_batalha.insert(0, mensagem_log)

                # --- PROCESSAMENTO FIM DE TURNO DO POKÉMON ATIVO ---
                if pk_atkr["disable"]:
                    pk_atkr["disable_turnos"] -= 1
                    if pk_atkr["disable_turnos"] <= 0: pk_atkr["disable"] = None

                if pk_atkr["status"] == "Envenenado" and pk_atkr["hp"] > 0:
                    pk_atkr["hp"] -= max(3, int(pk_atkr["hp_max"] * 0.04))
                    st.session_state.log_batalha.insert(0, f"🤢 **{nome_atacante}** sofreu dano do Veneno!")
                
                if pk_atkr["status"] == "Toxic" and pk_atkr["hp"] > 0:
                    dano_tox = max(4, int(pk_atkr["hp_max"] * (0.03 * pk_atkr["toxic_turnos"])))
                    pk_atkr["hp"] -= dano_tox
                    st.session_state.log_batalha.insert(0, f"☣️ O Toxic causou **{dano_tox}** de dano em **{nome_atacante}**!")
                    if pk_atkr["toxic_turnos"] >= 5: pk_atkr["status"] = None; pk_atkr["toxic_turnos"] = 0
                    else: pk_atkr["toxic_turnos"] += 1

                if pk_atkr["status"] == "Queimado" and pk_atkr["hp"] > 0:
                    pk_atkr["hp"] -= max(4, int(pk_atkr["hp_max"] * 0.06))
                    st.session_state.log_batalha.insert(0, f"🔥 **{nome_atacante}** sofreu dano da Queimadura!")

                if st.session_state.clima != "Normal":
                    st.session_state.clima_turnos -= 1
                    if st.session_state.clima_turnos <= 0: st.session_state.clima = "Normal"

                # Cálculo de Velocidade de turno extra
                sp_a = pk1["stats_base"]["speed"] * calcular_modificador_estagio(pk1["estagios"]["speed"]) * (0.5 if pk1["status"] == "Paralisado" else 1.0)
                sp_b = pk2["stats_base"]["speed"] * calcular_modificador_estagio(pk2["estagios"]["speed"]) * (0.5 if pk2["status"] == "Paralisado" else 1.0)
                speed_atk = sp_a if jogador_atual == 1 else sp_b
                speed_def = sp_b if jogador_atual == 1 else sp_a

                if pode_atacar and speed_atk >= speed_def * 4.0 and st.session_state.turnos_extras < 1:
                    st.session_state.turnos_extras += 1
                    st.session_state.log_batalha.insert(0, f"💨 Agilidade insana do **{nome_atacante}**! Ganhou um turno extra!")
                else:
                    st.session_state.turno = 2 if jogador_atual == 1 else 1
                    st.session_state.turnos_extras = 0

                st.rerun()

        with st.expander("📝 Histórico Completo da Arena", expanded=True):
            for linha in st.session_state.log_batalha: st.write(linha)
                
        st.write("---")
        if st.button("Fugir da batalha 🏳️"): st.session_state.batalha_ativa = False; st.rerun()