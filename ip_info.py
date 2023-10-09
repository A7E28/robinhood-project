import socket
import ipwhois
import whois
from telethon import events

# Define a function to handle the /ip_info command
async def ip_info_command(event):
    # Get the user's input (the IP address or domain name)
    user_input = event.text.split(" ", 1)
    
    if len(user_input) != 2:
        await event.reply("Please provide an IP address or domain name.")
        return
    
    query = user_input[1].strip()
    
    try:
        is_ip_address, ip_address = is_valid_ip(query)
        
        if is_ip_address:
            result = lookup_ip_info(ip_address)
            info_message = format_ip_info(result, query)
        else:
            ip_address = resolve_domain(query)
            
            if not ip_address:
                await event.reply(f"Failed to resolve the domain: {query}")
                return
            
            result = lookup_ip_info(ip_address)
            info_message = format_ip_info(result, ip_address)
            
            # Reverse DNS Lookup
            hostname = reverse_dns_lookup(ip_address)
            info_message += f"Reverse DNS: {hostname}\n"
            
            domain_info = get_domain_info(query)
            
            info_message += f"Registrar: {domain_info['registrar']}\n"
            info_message += f"Creation Date: {domain_info['creation_date']}\n"
            info_message += f"Expiration Date: {domain_info['expiration_date']}\n"
            info_message += f"Name Servers: {', '.join(domain_info['name_servers'])}\n"
        
        # Add location information
        location_info = get_location_info(result)
        info_message += f"Location: {location_info}\n"
        
        await event.reply(info_message)
    except ipwhois.exceptions.IPDefinedError:
        await event.reply("Invalid IP address or domain name.")
    except Exception as e:
        await event.reply(f"An error occurred: {str(e)}")

# Function to check if the input is a valid IP address
def is_valid_ip(input_str):
    try:
        socket.inet_pton(socket.AF_INET, input_str)
        return True, input_str
    except socket.error:
        return False, None

# Function to perform IP WHOIS lookup
def lookup_ip_info(ip_address):
    obj = ipwhois.IPWhois(ip_address)
    result = obj.lookup_rdap()
    return result

# Function to resolve a domain name to an IP address
def resolve_domain(domain):
    try:
        ip_address = socket.gethostbyname(domain)
        return ip_address
    except socket.gaierror:
        return None

# Function for reverse DNS lookup
def reverse_dns_lookup(ip_address):
    try:
        hostname = socket.gethostbyaddr(ip_address)[0]
        return hostname
    except socket.herror:
        return "N/A"

# Function to get domain information using the 'whois' library
def get_domain_info(domain):
    domain_info = whois.whois(domain)
    registrar = domain_info.registrar if domain_info.registrar else 'N/A'
    creation_date = domain_info.creation_date[0].strftime('%Y-%m-%d') if domain_info.creation_date else 'N/A'
    expiration_date = domain_info.expiration_date[0].strftime('%Y-%m-%d') if domain_info.expiration_date else 'N/A'
    name_servers = domain_info.name_servers if domain_info.name_servers else []
    
    return {
        'registrar': registrar,
        'creation_date': creation_date,
        'expiration_date': expiration_date,
        'name_servers': name_servers
    }

# Function to format IP information
def format_ip_info(result, query):
    info_message = f"Information for {query}:\n\n"
    info_message += f"IP Address: {result['query']}\n"
    info_message += f"Registry: {result['asn_registry']}\n"
    info_message += f"Country: {result['asn_country_code']}\n"
    info_message += f"Organization: {result['asn_description']}\n"
    info_message += f"IP Range: {result['network']['cidr']}\n"

    # Check if 'name_servers' field exists in the result
    if 'name_servers' in result:
        info_message += f"Name Servers: {', '.join(result['name_servers'])}\n"
    
    # Additional details
    info_message += f"IP Version: {result['network']['ip_version']}\n"
    info_message += f"Allocated Date: {result['asn_date']}\n"
    info_message += f"IP Type: {result['network']['type']}\n"
    
    return info_message

# Function to retrieve location information
def get_location_info(result):
    location_info = result.get('city', result.get('asn_country_code', 'N/A'))
    return location_info

# Register the /ip_info command handler with the client
def register_ip_info_feature(client):
    @client.on(events.NewMessage(pattern='/ip_info'))
    async def ip_info_handler(event):
        await ip_info_command(event)
